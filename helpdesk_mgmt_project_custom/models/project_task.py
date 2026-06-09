from odoo import api, fields, models
from odoo.tools.translate import _


class ProjectTask(models.Model):
    _inherit = "project.task"

    ticket_ids = fields.One2many(
        comodel_name="helpdesk.ticket", 
        inverse_name="task_id", 
        string="Tickets"
    )
    
    ticket_count = fields.Integer(compute="_compute_ticket_count")
    
    label_tickets = fields.Char(
        string="Use Tickets as",
        default=lambda self: _("Tickets"),
        translate=True,
        help="Gives label to tickets on project's kanban view.",
    )
    
    todo_ticket_count = fields.Integer(
        string="Number of tickets", 
        compute="_compute_ticket_count"
    )

    @api.depends("ticket_ids", "ticket_ids.stage_id")
    def _compute_ticket_count(self):
        HelpdeskTicket = self.env["helpdesk.ticket"]
        invname = "task_id"
        domain = [(invname, "in", self.ids)]
        fields = [invname]
        groupby = [invname]
        
        counts = {
            pr[invname][0]: pr[f"{invname}_count"]
            for pr in HelpdeskTicket.read_group(domain, fields, groupby)
        }
        
        domain.append(("closed", "=", False))
        counts_todo = {
            pr[invname][0]: pr[f"{invname}_count"]
            for pr in HelpdeskTicket.read_group(domain, fields, groupby)
        }
        
        for record in self:
            record.ticket_count = counts.get(record.id, 0)
            record.todo_ticket_count = counts_todo.get(record.id, 0)

    def action_open_helpdesk_tickets_from_task(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "helpdesk_mgmt_project_custom.ticket_action_from_project"
        )
        action["domain"] = [("task_id", "=", self.id)]
        action["context"] = {
            "default_project_id": self.project_id.id,
            "default_task_id": self.id,
        }
        return action