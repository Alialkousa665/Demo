from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from odoo.tools.misc import get_lang
import logging
from odoo.exceptions import UserError



class ResPartner(models.Model):
    _inherit = 'res.partner'

    responsible_salesperson_id = fields.Many2one('res.users', string='Responsible Salesperson')
    contact_type = fields.Selection([
        ('customer', 'Customer'),
        ('lead', 'Lead'),
        ('vendor', 'Vendor'),
        ('employee', 'Employee')
    ], string='Contact Type')
    def _send_internal_message(self, contact):
        if contact:
            self.message_post(body=f"Starting communication with {self.name}", partner_ids=[contact.id])
        else:
            raise UserError(f"Contact {contact.name} does not exist.")


class EventManagement(models.Model):
    _name = 'event.management'
    _description = 'Event Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Event Name', required=True)
    date = fields.Date(string='Event Date', required=True)
    communication_start_before = fields.Integer(string='Communication Start Before (Days)', required=True)
    contact_ids = fields.Many2many('res.partner', string='Contacts')

    @api.model
    def _send_event_reminders(self):
        today = fields.Date.today()
        print("running crom job>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        events = self.search([('date', '>=', today)])
        for event in events:
            communication_start_date = event.date - timedelta(days=event.communication_start_before)
            print("sdasdasdasdasdasdasdasd")
            print(communication_start_date)
            if communication_start_date <= today:
                print("Notify SAles Person >>>>>>>>>>")
                
                self._notify_salespersons(event)
               

    def _send_system_notification(self, salesperson, event, contacts):
        print("SALES PERSONMNQWE")
        print(salesperson)
        for contact in contacts:
            user_id = salesperson.id
            activity_type = self.env.ref('xyz.mail_act_event_notification')
            message = f"Starting communication for event {event.name}"
            # self.activity_schedule('mail_act_event_notification', user_id= '2' ,note=f'Please Check  Event  {self.name}')
            activity = self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': ' activity summary',
                'note': f"Starting communication for event {event.name}",
                'res_id': event,
                'res_model_id': self.env.ref('xyz.model_event_management').id,
                'user_id': user_id,
                'date_deadline': fields.Date.today() + timedelta(days=7)  # Example: set a deadline 7 days from now
            })
            return activity
 

    def _notify_salespersons(self, event):
        salespersons = event.contact_ids.mapped('responsible_salesperson_id')
        for salesperson in salespersons:
            contacts = event.contact_ids.filtered(lambda c: c.responsible_salesperson_id == salesperson)
            
            self._send_system_notification(salesperson, event, contacts)
            self._send_email(salesperson, event, contacts)
            # self._send_email(salesperson, event, contacts)
    def _send_email(self, salesperson, event, contacts):
        print("Send Email SELF SALES PERSON")
        ctx = {}
        salespersons = event.contact_ids.mapped('responsible_salesperson_id')
        for salesperson in salespersons:
            email_to=salesperson.email
            if email_to:
                ctx['email_to'] = email_to
                ctx['email_from'] = self.env.user.company_id.email
                ctx['send_email'] = True
               
                template = self.env.ref('xyz.event_reminder_email_template')
                template.with_context(ctx).send_mail(self.id, force_send=True, raise_exception=False)

        print("Finish Send mail ")

    def _build_email_body(self, event, contacts):
        print("TRack Build email body")
        contacts_html = "<ul>"
        for contact in contacts:
            contacts_html += f"<li>{contact.name}</li>"
        contacts_html += "</ul>"
        body = f"""
            <p>Hello,</p>
            <p>This is a reminder for the upcoming event: {event.name}</p>
            <p>Event Date: {event.date}</p>
            <p>Please start communication with the following contacts:</p>
            {contacts_html}
            <p><a href="/web#id={event.id}&view_type=form&model=event.management">Click here to view the event details</a></p>
        """
        return body

   

    