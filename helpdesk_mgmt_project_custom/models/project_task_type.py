from odoo import api, models


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    @api.model
    def _get_or_create_cancelled_stage(self, project=None):
        """
        Obtiene la etapa 'Cancelado' del proyecto dado.
        Si no existe, la crea y la vincula al proyecto.
        """
        domain = [("name", "=", "Cancelado"), ("fold", "=", True)]
        if project:
            domain.append(("project_ids", "in", project.id))

        stage = self.search(domain, limit=1)

        if not stage:
            # Buscar sin filtro de proyecto y vincular, o crear nueva
            stage = self.search(
                [("name", "=", "Cancelado"), ("fold", "=", True)], limit=1
            )
            if not stage:
                stage = self.create({
                    "name": "Cancelado",
                    "fold": True,
                    "sequence": 990,
                })
            if project and project not in stage.project_ids:
                stage.write({"project_ids": [(4, project.id)]})

        elif project and project not in stage.project_ids:
            stage.write({"project_ids": [(4, project.id)]})

        return stage

    @api.model
    def _get_or_create_rejected_stage(self, project=None):
        """
        Obtiene la etapa 'Rechazado' del proyecto dado.
        Si no existe, la crea y la vincula al proyecto.
        """
        domain = [("name", "=", "Rechazado"), ("fold", "=", True)]
        if project:
            domain.append(("project_ids", "in", project.id))

        stage = self.search(domain, limit=1)

        if not stage:
            stage = self.search(
                [("name", "=", "Rechazado"), ("fold", "=", True)], limit=1
            )
            if not stage:
                stage = self.create({
                    "name": "Rechazado",
                    "fold": True,
                    "sequence": 991,
                })
            if project and project not in stage.project_ids:
                stage.write({"project_ids": [(4, project.id)]})

        elif project and project not in stage.project_ids:
            stage.write({"project_ids": [(4, project.id)]})

        return stage