from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"
    
    # Añadir nuevos campos
    is_cancelled = fields.Boolean(string="Is Cancelled", default=False)
    is_rejected = fields.Boolean(string="Is Rejected", default=False)

    project_id = fields.Many2one(
        string="Project",
        comodel_name="project.project",
        tracking=True,
    )

    task_ids = fields.Many2many(
        string="Tasks",
        comodel_name="project.task",
        relation="helpdesk_ticket_project_task_rel",
        column1="ticket_id",
        column2="task_id",
        tracking=True,
    )

    milestone_id = fields.Many2one(
        "project.milestone",
        store=True,
        tracking=True,
        readonly=False,
        compute="_compute_milestone_id",
    )

    @api.depends("task_ids.milestone_id")
    def _compute_milestone_id(self):
        for record in self:
            record.milestone_id = (
                record.task_ids[:1].milestone_id if record.task_ids else False
            )

    @api.onchange("project_id")
    def _onchange_project_id(self):
        """Filter tasks when project changes."""
        for record in self:
            if record.project_id:
                record.task_ids = record.task_ids.filtered(
                    lambda t: t.project_id == record.project_id
                )
            else:
                record.task_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        for ticket in tickets:
            if ticket.closed and ticket.task_ids:
                ticket._sync_tasks_stage()
            if ticket.stage_id and ticket.stage_id.fold and ticket.task_ids:
                ticket._sync_tasks_from_stage()
            if ticket.is_cancelled or ticket.is_rejected:
                ticket._sync_tasks_cancelled_rejected()
        return tickets

    def write(self, vals):
        result = super().write(vals)

        is_cancelling = 'is_cancelled' in vals and vals.get('is_cancelled')
        is_rejecting  = 'is_rejected'  in vals and vals.get('is_rejected')

        if is_cancelling or is_rejecting:
            for ticket in self:
                if ticket.task_ids:
                    ticket._sync_tasks_cancelled_rejected()
            return result

        if 'closed' in vals and vals.get('closed'):
            for ticket in self:
                if ticket.task_ids and not ticket.is_cancelled and not ticket.is_rejected:
                    ticket._sync_tasks_stage()

        if 'is_cancelled' in vals and not vals.get('is_cancelled', True):
            for ticket in self:
                if ticket.task_ids:
                    ticket._sync_tasks_unmark()

        if 'is_rejected' in vals and not vals.get('is_rejected', True):
            for ticket in self:
                if ticket.task_ids:
                    ticket._sync_tasks_unmark()

        if 'stage_id' in vals:
            for ticket in self:
                if ticket.is_cancelled or ticket.is_rejected:
                    continue
                if ticket.task_ids:
                    if ticket.stage_id and ticket.stage_id.fold:
                        ticket._sync_tasks_from_stage()
                    elif not ticket.stage_id.fold and ticket.closed:
                        ticket.write({'closed': False})
        
        if 'task_ids' in vals:
            for ticket in self:
                ticket._sync_ticket_closed_from_tasks()
        
        return result

    def _sync_tasks_stage(self):
        """Sincronizar tareas cuando el ticket se cierra"""
        for ticket in self:
            if ticket.closed and ticket.task_ids and not ticket.is_cancelled and not ticket.is_rejected:
                for task in ticket.task_ids:
                    task.action_mark_as_done()

    def _sync_tasks_cancelled_rejected(self):
        """Mover tareas a Cancelado/Rechazado"""
        for ticket in self:
            if not ticket.task_ids:
                continue
            if ticket.is_rejected:
                for task in ticket.task_ids:
                    task._move_to_rejected_stage()
            elif ticket.is_cancelled:
                for task in ticket.task_ids:
                    task._move_to_cancelled_stage()
            if not ticket.closed:
                ticket.write({'closed': True})
    
    def _sync_tasks_unmark(self):
        """Resetear tareas al desmarcar"""
        for ticket in self:
            if ticket.task_ids and not ticket.closed and not ticket.is_cancelled and not ticket.is_rejected:
                for task in ticket.task_ids:
                    if task.is_done:
                        task.action_mark_as_pending()

    def _sync_tasks_from_stage(self):
        """Sincronizar cuando ticket llega a etapa final"""
        for ticket in self:
            if ticket.stage_id and ticket.stage_id.fold and ticket.task_ids:
                for task in ticket.task_ids:
                    if not task.is_done:
                        task.action_mark_as_done()
                if not ticket.closed:
                    ticket.write({'closed': True})

    def _sync_ticket_closed_from_tasks(self):
        """Cerrar ticket cuando todas las tareas están completadas"""
        for ticket in self:
            if ticket.task_ids and not ticket.closed and not ticket.is_cancelled and not ticket.is_rejected:
                all_tasks_done = all(task.is_done for task in ticket.task_ids)
                if all_tasks_done:
                    ticket.write({'closed': True})
                    # CORREGIDO: Acceso seguro a stages del equipo
                    if ticket.team_id:
                        done_stage = ticket.team_id.stage_ids.filtered(
                            lambda s: s.fold
                        ).sorted('sequence')[:1] if hasattr(ticket.team_id, 'stage_ids') else False
                        if done_stage:
                            ticket.write({'stage_id': done_stage.id})
    
    def action_cancel_ticket(self):
        """Cancelar ticket"""
        for ticket in self:
            ticket.write({'is_cancelled': True, 'closed': True})
            for task in ticket.task_ids:
                task._move_to_cancelled_stage()
            ticket.task_ids._compute_ticket_states()
        return True

    def action_reject_ticket(self):
        """Rechazar ticket"""
        for ticket in self:
            ticket.write({'is_rejected': True, 'closed': True})
            for task in ticket.task_ids:
                task._move_to_rejected_stage()
            ticket.task_ids._compute_ticket_states()
        return True

    def action_unmark_ticket(self):
        """Desmarcar ticket"""
        for ticket in self:
            ticket.write({'is_cancelled': False, 'is_rejected': False, 'closed': False})
            for task in ticket.task_ids:
                task.action_mark_as_pending()
            ticket.task_ids._compute_ticket_states()
        return True