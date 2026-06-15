from odoo import api, fields, models
from odoo.tools.translate import _


class ProjectTask(models.Model):
    _inherit = "project.task"

    ticket_ids = fields.Many2many(
        comodel_name="helpdesk.ticket",
        relation="helpdesk_ticket_project_task_rel",
        column1="task_id",
        column2="ticket_id",
        string="Tickets",
    )

    ticket_count = fields.Integer(compute="_compute_ticket_count")
    todo_ticket_count = fields.Integer(compute="_compute_ticket_count")

    is_done = fields.Boolean(
        string="Is Done",
        compute="_compute_is_done",
        store=True,
    )

    has_cancelled_ticket = fields.Boolean(
        string="Has Cancelled Ticket",
        compute="_compute_ticket_states",
        store=True,
    )

    has_rejected_ticket = fields.Boolean(
        string="Has Rejected Ticket",
        compute="_compute_ticket_states",
        store=True,
    )

    has_open_ticket = fields.Boolean(
        string="Has Open Ticket",
        compute="_compute_ticket_states",
        store=True,
    )

    @api.depends("ticket_ids", "ticket_ids.is_cancelled", "ticket_ids.is_rejected", "ticket_ids.closed")
    def _compute_ticket_states(self):
        for task in self:
            if task.ticket_ids:
                task.has_cancelled_ticket = any(t.is_cancelled for t in task.ticket_ids)
                task.has_rejected_ticket = any(t.is_rejected for t in task.ticket_ids)
                task.has_open_ticket = any(
                    not t.closed and not t.is_cancelled and not t.is_rejected
                    for t in task.ticket_ids
                )
            else:
                task.has_cancelled_ticket = False
                task.has_rejected_ticket = False
                task.has_open_ticket = False

    @api.depends("stage_id.fold")
    def _compute_is_done(self):
        """Una tarea está completada si está en una etapa plegada (fold=True)."""
        for task in self:
            task.is_done = bool(task.stage_id.fold)

    @api.depends("ticket_ids", "ticket_ids.closed")
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids)
            record.todo_ticket_count = len(
                record.ticket_ids.filtered(lambda t: not t.closed)
            )

    def action_open_helpdesk_tickets_from_task(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "helpdesk_mgmt_project_custom.ticket_action_from_project"
        )
        action["domain"] = [("task_ids", "in", self.ids)]
        action["context"] = {
            "default_task_ids": [(4, self.id)],
            "default_project_id": self.project_id.id,
        }
        return action

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        project_id = self.env.context.get("default_project_id") or defaults.get("project_id")
        if project_id and "stage_id" in fields_list:
            project = self.env["project.project"].browse(project_id)
            if project.exists() and project.type_ids:
                special = self._get_special_stage_ids()
                default_stage = project.type_ids.filtered(
                    lambda s: not s.fold and s.id not in special
                ).sorted("sequence")[:1]
                if default_stage:
                    defaults["stage_id"] = default_stage.id
                elif project.type_ids:
                    defaults["stage_id"] = project.type_ids[:1].id
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "stage_id" not in vals and "project_id" in vals:
                project = self.env["project.project"].browse(vals["project_id"])
                if project.exists() and project.type_ids:
                    special = self._get_special_stage_ids()
                    default_stage = project.type_ids.filtered(
                        lambda s: not s.fold and s.id not in special
                    ).sorted("sequence")[:1]
                    if default_stage:
                        vals["stage_id"] = default_stage.id
                    elif project.type_ids:
                        vals["stage_id"] = project.type_ids[:1].id
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)

        # === LÓGICA AL CAMBIAR DE ETAPA ===
        if "stage_id" in vals:
            for task in self:
                new_stage = task.stage_id
                special = task._get_special_stage_ids()

                # Si pasa a etapa normal (En Espera / En Proceso)
                if new_stage and not new_stage.fold and new_stage.id not in special:
                    if task.ticket_ids and (task.has_cancelled_ticket or task.has_rejected_ticket):
                        task.action_unmark_linked_tickets()

                # Si pasa a etapa final
                elif new_stage and new_stage.fold and new_stage.id not in special:
                    if task.ticket_ids:
                        for ticket in task.ticket_ids:
                            if not ticket.closed and not ticket.is_cancelled and not ticket.is_rejected:
                                all_tasks_done = all(t.is_done for t in ticket.task_ids)
                                if all_tasks_done:
                                    ticket.write({"closed": True})
                                    # ACCESO SEGURO - Evita error en helpdesk.team
                                    if ticket.team_id and hasattr(ticket.team_id, 'stage_ids'):
                                        done_stage = ticket.team_id.stage_ids.filtered(
                                            lambda s: s.fold
                                        ).sorted('sequence')[:1]
                                        if done_stage:
                                            ticket.write({"stage_id": done_stage.id})

        return result

    # ------------------------------------------------------------------
    # Helpers para etapas especiales
    # ------------------------------------------------------------------

    @api.model
    def _get_special_stage_ids(self):
        """Devuelve los IDs de las etapas Cancelado y Rechazado."""
        TaskType = self.env["project.task.type"]
        special = set()
        cancelled = TaskType.search([("name", "=", "Cancelado"), ("fold", "=", True)], limit=1)
        rejected = TaskType.search([("name", "=", "Rechazado"), ("fold", "=", True)], limit=1)
        if cancelled:
            special.add(cancelled.id)
        if rejected:
            special.add(rejected.id)
        return special

    def _move_to_cancelled_stage(self):
        TaskType = self.env["project.task.type"]
        for task in self:
            stage = TaskType._get_or_create_cancelled_stage(project=task.project_id)
            if stage:
                task.write({"stage_id": stage.id})

    def _move_to_rejected_stage(self):
        TaskType = self.env["project.task.type"]
        for task in self:
            stage = TaskType._get_or_create_rejected_stage(project=task.project_id)
            if stage:
                task.write({"stage_id": stage.id})

    # ------------------------------------------------------------------
    # Marcar como hecho / pendiente
    # ------------------------------------------------------------------

    def action_mark_as_done(self):
        self.ensure_one()
        special = self._get_special_stage_ids()
        done_stage = False

        if self.project_id and self.project_id.type_ids:
            done_stage = self.project_id.type_ids.filtered(
                lambda s: s.fold and s.id not in special
            ).sorted("sequence")[:1]

        if not done_stage:
            done_stage = self.env["project.task.type"].search(
                [("fold", "=", True), ("id", "not in", list(special))], limit=1
            )

        if done_stage:
            self.write({"stage_id": done_stage.id})
            return True

        if not self.env.context.get("skip_warning"):
            return {
                "warning": {
                    "title": _("No hay etapa final"),
                    "message": _(
                        "No se ha definido ninguna etapa marcada como 'Hecho' (fold=True) "
                        "para este proyecto. Por favor, configure las etapas del proyecto."
                    ),
                }
            }
        return False

    def action_mark_as_pending(self):
        special = self._get_special_stage_ids()
        for task in self:
            pending_stage = False
            if task.project_id and task.project_id.type_ids:
                pending_stage = task.project_id.type_ids.filtered(
                    lambda s: not s.fold and s.id not in special
                ).sorted("sequence")[:1]
            if pending_stage:
                task.write({"stage_id": pending_stage.id})
        return True

    # ==================================================================
    # BOTONES DE CANCELAR / RECHAZAR / DESMARCAR
    # ==================================================================

    def action_cancel_linked_tickets(self):
        self.ensure_one()
        if not self.ticket_ids:
            return
        for ticket in self.ticket_ids:
            ticket.action_cancel_ticket()
        self._compute_ticket_states()
        return True

    def action_reject_linked_tickets(self):
        self.ensure_one()
        if not self.ticket_ids:
            return
        for ticket in self.ticket_ids:
            ticket.action_reject_ticket()
        self._compute_ticket_states()
        return True

    def action_unmark_linked_tickets(self):
        self.ensure_one()
        if not self.ticket_ids:
            return
        for ticket in self.ticket_ids:
            ticket.action_unmark_ticket()
        self._compute_ticket_states()
        return True