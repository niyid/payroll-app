#-*- coding:utf-8 -*-
# Part of ChamsERP. See LICENSE file for full copyright and licensing details.
import time, re, logging, gc, smtplib
from itertools import compress
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, models, netsvc, registry
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)
_logger2 = logging.getLogger(__name__)

class res_users(osv.osv):
    _inherit = 'res.users'
    
    _columns = {
        'domain_mdas': fields.many2many('hr.department', 'rel_user_domain_mdas', 'user_id', 'department_id', 'Domain MDAs',),                
    }

class hr_employee(osv.osv):
    '''
    Employee
    '''

    _inherit = "hr.employee"
    _description = 'Employee'

    _columns = {
        'sinid': fields.char('Pension PIN', help='Pension PIN'),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'resolved_earn_dedt': fields.boolean('Active', help='Active Status', required=False),
        'employee_no': fields.char('Employee Number', help='Employee Number'),
        'school_emp_id': fields.char('School Employee ID', help='School Employee ID', required=False),
        'bank_account_no': fields.char('Bank Account', help='Bank Account Number'),
        'hire_date': fields.date('Hire Date', help='Date of Hire'),
        'confirmation_date': fields.date('Confirmation Date', help='Date of Confirmation'),
        'retirement_due_date': fields.date('Retirement-Due Date', help='Retirement-Due Date'),
        'last_promotion_date': fields.date('Last Promotion Date', help='Last Promotion Date'),
        'next_promotion_date': fields.date('Next Promotion Date', help='Next Promotion Date'),
        'lga_id': fields.many2one('ng.state.payroll.lga', 'LGA'),
        'pfa_id': fields.many2one('ng.state.payroll.pfa', 'PFA'),
        'school_id': fields.many2one('ng.state.payroll.school', 'School', required=False),
        'paycategory_id': fields.many2one('ng.state.payroll.paycategory', 'Step'),
        'payscheme_id': fields.many2one('ng.state.payroll.payscheme', 'Pay Scheme'),
        'level_id': fields.many2one('ng.state.payroll.level', 'Level'),
        'grade_level': fields.selection([
            (1, 'GL-1'),
            (2, 'GL-2'),
            (3, 'GL-3'),
            (4, 'GL-4'),
            (5, 'GL-5'),
            (6, 'GL-6'),
            (7, 'GL-7'),
            (8, 'GL-8'),
            (9, 'GL-9'),
            (10, 'GL-10'),
            (12, 'GL-12'),
            (13, 'GL-13'),
            (14, 'GL-14'),
            (15, 'GL-15'),
            (16, 'GL-16'),
            (17, 'GL-17'),
        ], 'Grade Level'),
        'title_id': fields.many2one('res.partner.title', 'Title'),
        'status_id': fields.many2one('ng.state.payroll.status', 'Employee Status'),
        'bank_id': fields.many2one('res.bank', string='Bank'),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=False),
        'disciplinary_actions': fields.one2many('ng.state.payroll.disciplinary', 'employee_id', 'Disciplinary Actions'),
        'promotions': fields.one2many('ng.state.payroll.promotion', 'employee_id', 'Promotions'),
        'salary_items': fields.one2many('ng.state.payroll.payroll.item', 'employee_id', 'Salary History'),
        'payment_items': fields.one2many('ng.state.payroll.scenario.payment', 'employee_id', 'Payment History'),
        'query_items': fields.one2many('ng.state.payroll.query', 'employee_id', 'Query History'),
        'pensiontype_id': fields.many2one('ng.state.payroll.pensiontype', 'Pension Type', required=False),
        'tco_id': fields.many2one('ng.state.payroll.tco', 'TCO', required=False),
        'pensionfile_no': fields.char('Pension File', help='Pension File Number'),
        'annual_pension': fields.float('Annual Pension', help='Annual Pension'),
        'standard_earnings': fields.many2many('ng.state.payroll.earning.standard', 'rel_employee_std_earning', 'employee_id','earning_id', 'Standard Earnings'), 
        'standard_deductions': fields.many2many('ng.state.payroll.deduction.standard', 'rel_employee_std_deduction', 'employee_id','deduction_id', 'Standard Deductions'), 
        'nonstd_earnings': fields.one2many('ng.state.payroll.earning.nonstd', 'employee_id', 'Nonstandard Earnings'),
        'nonstd_deductions': fields.one2many('ng.state.payroll.deduction.nonstd', 'employee_id', 'Nonstandard Deduction'),
        'employee_earnings': fields.one2many('ng.state.payroll.earning.employee', 'employee_id', 'Employee Earnings'),
        'employee_deductions': fields.one2many('ng.state.payroll.deduction.employee', 'employee_id', 'Employee Deduction'),
    }
    
class hr_department(osv.osv):
    _name = "hr.department"
    _description = "Organization"
    _inherit = 'hr.department'

    _columns = {
        'name': fields.char('MDA', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'company_id': fields.many2one('res.company', 'Organization', select=True, required=False),
        'parent_id': fields.many2one('hr.department', 'Parent MDA', select=True),
        'orgtype_id': fields.many2one('ng.state.payroll.orgtype', 'MDA Type', select=True),
        'child_ids': fields.one2many('hr.department', 'parent_id', 'Child MDAs'),
        'member_ids': fields.one2many('hr.employee', 'department_id', 'Employees', readonly=True),
    } 
    
class ng_state_payroll_school(models.Model):
    _name = "ng.state.payroll.school"
    _description = "School"

    _columns = {
        'name': fields.char('School Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'org_id': fields.many2one('hr.department', 'Parent Organization', select=True),
    }  
           
class ng_state_payroll_relief(models.Model):
    '''
    Relief
    '''
    _name = "ng.state.payroll.relief"
    _description = 'Relief'

    _columns = {
        'name': fields.char('Relief', help='Relief Name', required=True),
        'code': fields.char('Code', help='Relief Code', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }  

    _defaults = {
        'active': True,
    }             
           
class ng_state_payroll_pensiontype(models.Model):
    '''
    Pension Type
    '''
    _name = "ng.state.payroll.pensiontype"
    _description = 'Pension Type'

    _columns = {
        'name': fields.char('Type', help='Pension Type Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }  

    _defaults = {
        'active': True,
    }             

class ng_state_payroll_orgtype(models.Model):
    '''
    Organization Type
    '''
    _name = "ng.state.payroll.orgtype"
    _description = 'Organization Type'

    _columns = {
        'name': fields.char('Type', help='Organization Type Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }       

    _defaults = {
        'active': True,
    }             

class ng_state_payroll_tco(models.Model):
    '''
    Treasury Cash Office
    '''
    _name = "ng.state.payroll.tco"
    _description = 'Treasury Cash Office'

    _columns = {
        'name': fields.char('TCO Name', help='Treasury Cash Office', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }

    _defaults = {
        'active': True,
    }             

class ng_state_payroll_lga(models.Model):
    '''
    Local Government Area
    '''
    _name = "ng.state.payroll.lga"
    _description = 'Local Government Areas'

    _columns = {
        'name': fields.char('LGA Name', help='Local Government Area', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'country_state': fields.many2one('res.country.state', 'Country State', required=True),
    }

    _defaults = {
        'active': True,
    }             

class ng_state_payroll_pfa(models.Model):
    '''
    Pension Fund Administrator
    '''
    _name = "ng.state.payroll.pfa"
    _description = 'Pension Fund Administrator'

    _columns = {
        'name': fields.char('PFA Name', help='Pension Fund Administrator Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }

    _defaults = {
        'active': True,
    }             
          
class ng_state_payroll_status(models.Model):
    '''
    Employee Status
    '''
    _name = "ng.state.payroll.status"
    _description = 'Employee Status'

    _columns = {
        'name': fields.char('Name', help='Employee Status', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
    }    

    _defaults = {
        'active': True,
    }             
    
class ng_state_payroll_paycategory(models.Model):
    '''
    Step
    '''
    _name = "ng.state.payroll.paycategory"
    _description = 'Step'

    _columns = {
        'name': fields.char('Name', help='Step', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'department': fields.many2one('hr.department', 'MDA', required=True),
    }

    _defaults = {
        'active': True,
    }             

class ng_state_payroll_level(models.Model):
    '''
    Level
    '''
    _name = "ng.state.payroll.level"
    _description = 'Level'
    
    _columns = {
        'name': fields.integer('Level', help='Level', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'pay_grade': fields.many2one('ng.state.payroll.paygrade', 'Pay Grade', required=True),
    }

    _defaults = {
        'active': True,
    }             
    
class ng_state_payroll_payscheme(models.Model):
    '''
    Pay Scheme
    '''
    _name = "ng.state.payroll.payscheme"
    _description = 'Pay Scheme'        

    _columns = {
        'name': fields.char('Name', help='Pay Scheme', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'use_dob': fields.boolean('Use DofB', help='Use birth date for retirement date computation', required=True),
        'use_dofa': fields.boolean('Use DofA', help='Use appointment date for retirement date computation', required=True),
        'retirement_age': fields.integer('Retirement Age', help='Expected retirement age', required=True),
        'service_years': fields.integer('Service Years', help='Number of years at which retirement is due', required=True),
    }

    _defaults = {
        'active': True,
        'use_dob': True,
        'use_dofa': True,
    }             
    
class ng_state_payroll_paygrade(models.Model):
    '''
    Pay Grade
    '''
    _name = "ng.state.payroll.paygrade"
    _description = 'Pay Grade'

    _columns = {
        'active': fields.boolean('Active', help='Active Status', required=True),
        'level_id': fields.many2one('ng.state.payroll.level', 'Level', required=True),
        'payscheme_id': fields.many2one('ng.state.payroll.payscheme', 'Pay Scheme', required=True),
    } 

    _defaults = {
        'active': True,
    }             

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for r in self.read(cr, uid, ids, ['id', 'level_id', 'payscheme_id'], context):
            aux = ('(')
            if r['level_id']:
                aux += ('Pay Level - ' + r['level_id'][1] + ', ') # same question
    
            if r['payscheme_id']:
                aux += ('Pay Scheme - ' + r['payscheme_id'][1]) # same question
            aux += (')')
    
            # aux is the name items for the r['id']
            res.append((r['id'], aux))  # append add the tuple (r['id'], aux) in the list res
    
        return res
    
class ng_state_payroll_deduction_pension(models.Model):
    '''
    Pension Deduction
    '''
    _name = "ng.state.payroll.deduction.pension"
    _description = 'Pension Deduction'

    _columns = {
        'name': fields.char('Name', help='Deduction Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'fixed': fields.boolean('Fixed Amount', help='Fixed Amount'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'whitelist_ids': fields.many2many('hr.employee', 'rel_deduction_pension_whitelist', 'deduction_id', 'employee_id', 'Whitelist', domain="[('status_id.name','=','PENSIONED'),('active','=',True)]",),
        'blacklist_ids': fields.many2many('hr.employee', 'rel_deduction_pension_blacklist', 'deduction_id', 'employee_id', 'Blacklist', domain="[('status_id.name','=','PENSIONED'),('active','=',True)]"),
    }

    _defaults = {
        'active': True,
    }             
        
class ng_state_payroll_deduction_standard(models.Model):
    '''
    Standard Deduction
    '''
    _name = "ng.state.payroll.deduction.standard"
    _description = 'Standard Deduction'

    _columns = {
        'name': fields.char('Name', help='Deduction Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'fixed': fields.boolean('Fixed Amount', help='Fixed Amount'),
        'relief': fields.boolean('Relief', help='Forming part of CRA Relief'),
        'income_deduction': fields.boolean('Income Deduction', help='Deducted from Income before CRA 20% calculation'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'payscheme_id': fields.many2one('ng.state.payroll.payscheme', 'Pay Scheme', required=True),
        'derived_from': fields.many2one('ng.state.payroll.earning.standard', 'Standard Earning'),
        'level_id': fields.many2one('ng.state.payroll.level', 'Level', required=True),
    }

    _defaults = {
        'active': True,
    }             
    
class ng_state_payroll_deduction_nonstd(models.Model):
    '''
    Non-Standard Deduction
    '''
    _name = "ng.state.payroll.deduction.nonstd"
    _description = 'Non-Standard Deduction'

    _columns = {
        'name': fields.char('Name', help='Deduction Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'permanent': fields.boolean('Permanent', help='Permanent'),
        'relief': fields.boolean('Relief', help='Forming part of CRF Relief'),
        'income_deduction': fields.boolean('Income Deduction', help='Deducted from Income before CRA 20% calculation'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'calendars': fields.many2many('ng.state.payroll.calendar', 'rel_deduction_nonstd_calendar', 'deduction_id','calendar_id', 'Calendars'),
    }

    _defaults = {
        'active': True,
        'permanent': False,
    }
    
class ng_state_payroll_earning_standard(models.Model):
    '''
    Standard Earning
    '''
    _name = "ng.state.payroll.earning.standard"
    _description = 'Standard Earning'

    _columns = {
        'name': fields.char('Name', help='Earning Name', required=True),
        'code': fields.char('Code', help='Rule Code', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'fixed': fields.boolean('Fixed Amount', help='Fixed Amount'),
        'taxable': fields.boolean('Taxable', help='Taxable'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'payscheme_id': fields.many2one('ng.state.payroll.payscheme', 'Pay Scheme', required=False),
        'level_id': fields.many2one('ng.state.payroll.level', 'Level', required=False),
        'derived_from': fields.many2one('ng.state.payroll.earning.standard', 'Standard Earning'),
    }

    _defaults = {
        'active': True,
    }             
        
class ng_state_payroll_earning_nonstd(models.Model):
    '''
    Non-Standard Earning
    '''
    _name = "ng.state.payroll.earning.nonstd"
    _description = 'Non-Standard Earning'

    _columns = {
        'name': fields.char('Name', help='Earning Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'permanent': fields.boolean('Permanent', help='Permanent'),
        'taxable': fields.boolean('Taxable', help='Taxable'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'calendars': fields.many2many('ng.state.payroll.calendar', 'rel_earning_nonstd_calendar', 'earning_id','calendar_id', 'Calendars'),
    }  

    _defaults = {
        'active': True,
        'permanent': False,
        'taxable': True,
    }
    
class ng_state_payroll_earning_employee(models.Model):
    '''
    Employee Earning
    '''
    _name = "ng.state.payroll.earning.employee"
    _description = 'Employee Earning'

    _columns = {
        'name': fields.char('Name', help='Earning Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'fixed': fields.boolean('Fixed Amount', help='Fixed Amount'),
        'taxable': fields.boolean('Taxable', help='Taxable'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'derived_from': fields.many2one('ng.state.payroll.earning.employee', 'Parent Earning'),
    }

    _defaults = {
        'active': True,
        'fixed': True,
    }   
            
class ng_state_payroll_deduction_employee(models.Model):
    '''
    Employee Deduction
    '''
    _name = "ng.state.payroll.deduction.employee"
    _description = 'Employee Deduction'

    _columns = {
        'name': fields.char('Name', help='Deduction Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'fixed': fields.boolean('Fixed Amount', help='Fixed Amount'),
        'amount': fields.float('Amount', help='Amount', required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'derived_from': fields.many2one('ng.state.payroll.earning.employee', 'Parent Earning'),
        'bank_account_id': fields.many2one('res.partner.bank', 'Deduction Bank Account', required=True),
    }

    _defaults = {
        'active': True,
        'fixed': True,
    }             
        
class ng_state_payroll_subvention(models.Model):
    '''
    Subvention
    '''
    _name = "ng.state.payroll.subvention"
    _description = 'Subvention'

    _columns = {
        'name': fields.char('Name', help='Earning Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'amount': fields.float('Amount', help='Amount', required=True),
        'calendar_id': fields.many2one('ng.state.payroll.calendar', 'Calendar', required=True, track_visibility='onchange'),
        'org_id': fields.many2one('hr.department', 'MDA', required=True, select=True),
    }

    _defaults = {
        'active': True,
    }             
       
class ng_state_payroll_salaryrule(models.Model):
    '''
    Salary Rule
    '''
    _name = "ng.state.payroll.salaryrule"
    _description = 'Salary Rule'

    _columns = {
        'code': fields.char('Code', help='Rule Code', required=True),
        'description': fields.char('Description', help='Rule Description', required=True),
    }
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code already exists!')
    ]
    
class ng_state_payroll_calendar(models.Model):
    '''
    Pay Calendar
    '''
    _name = "ng.state.payroll.calendar"
    _description = 'Pay Calendar'

    _columns = {
        'name': fields.char('Name', help='Deduction Name', required=False),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'org_id': fields.many2one('hr.department', 'MDA', required=True, select=True),
        'schedule_pay': fields.selection([
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('semi-annually', 'Semi-annually'),
            ('annually', 'Annually'),
            ('weekly', 'Weekly'),
            ('bi-weekly', 'Bi-weekly'),
            ('bi-monthly', 'Bi-monthly'),
            ], 'Scheduled Pay', required=True, select=True),
        'from_date': fields.date('From Date', help='From Date', required=True),
        'to_date': fields.date('To Date', help='To Date', required=True),
    }

    _defaults = {
        'active': True,
    }             

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for r in self.read(cr, uid, ids, ['id', 'from_date', 'to_date', 'name'], context):
            aux = ''
            if r['name']:
                aux = r['name']
    
            aux +=  " ("
            if r['from_date']:
                aux += datetime.strptime(r['from_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                # why translate a date? I think is a mistake, the _() function must have a 
                # known string, example _("the start date is %s") % r['from_date']
    
            aux +=  ' - '
            if r['to_date']:
                aux += datetime.strptime(r['to_date'], '%Y-%m-%d').strftime('%d/%m/%Y') # same question
    
            aux += ')'
    
            # aux is the name items for the r['id']
            res.append((r['id'], aux))  # append add the tuple (r['id'], aux) in the list res
    
        return res

        #Open create form with current month date range
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('id','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('to_date',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('from_date',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                    #End
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('id','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

class ng_state_payroll_taxrule(models.Model):
    '''
    Tax Rule
    '''
    _name = "ng.state.payroll.taxrule"
    _description = 'Tax Rule'

    _columns = {
        'name': fields.char('Name', help='Tax Rule Name', required=False),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'from_amount': fields.float('From Amount', help='From Amount', required=True),
        'to_amount': fields.float('To Amount', help='To Amount', required=True),
        'percentage': fields.float('Percentage', help='Percentage', required=True),
    }

    _defaults = {
        'active': True,
    }             

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for r in self.read(cr, uid, ids, ['id', 'name', 'from_amount', 'to_amount', 'percentage'], context):
            aux = ''
            if r['name']:
                aux = r['name']
                
            aux += '('
            if r['to_amount']:
                aux += str(r['to_amount'])

            aux += ' to '
            if r['to_amount']:
                aux += str(r['to_amount'])

            aux +=  ' @ '
            if r['percentage']:
                aux += (str(r['percentage']) + '%')

            aux += ')'
            # aux is the name items for the r['id']
            res.append((r['id'], aux))  # append add the tuple (r['id'], aux) in the list res
    
        return res

class ng_state_payroll_leaveallowance(models.Model):
    '''
    Leave Allowance
    '''
    _name = "ng.state.payroll.leaveallowance"
    _description = 'Leave Allowance'

    _columns = {
        'percentage': fields.float('Percentage', help='Percentage', required=True),
        'payscheme_id': fields.many2one('ng.state.payroll.payscheme', 'Pay Scheme', required=True),
    }
    
class ng_state_payroll_scenariobatch(models.Model):
    '''
    Scenario Batch
    '''
    _name = "ng.state.payroll.scenariobatch"
    _description = 'Scenario Batch'

    _columns = {
        'name': fields.char('Name', help='Scenario Name', required=True),
        'scenario_ids': fields.one2many('ng.state.payroll.scenario','batch_id','Scenarios'),
        'state': fields.selection([
            ('draft','Draft'),
            ('processed','Processed'),
            ('closed','Closed')
        ], 'Status')
    }
    
    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        res = super(ng_state_payroll_scenariobatch, self).create(vals)
            
        return res    
   
    @api.multi   
    def run_finalize(self):
        self.finalize()
   
    @api.multi   
    def run_dry_run(self):
        self.dry_run()

    @api.multi
    def dry_run(self, context=None):
        env = self.env
        with env.do_in_draft():
            res = self.finalize()
                   
        return res
         
    @api.multi
    def finalize(self):
        _logger.info("Calling finalize...state = %s", self.state)
        
        for scenario_id in self.scenario_ids:
            scenario_id.finalize()
        
        #TODO write processed if all scenarios completed successfully
        return self.write({'state':'processed'})  
    
class ng_state_payroll_scenario_signoff(models.Model):
    '''
    Payment Sign-Off
    '''
    _name = "ng.state.payroll.scenario.signoff"
    _description = 'Payment Sign-Off'

    _columns = {
        'scenario_id': fields.many2one('ng.state.payroll.scenario', 'Scenario', required=True),
        'user_id': fields.many2one('res.users', 'Payment Approver', required=True, domain="[('groups_id.name','=','Payroll Officer')]"),
        'signed_off': fields.boolean('Closed', help='Sign-Off closed status', required=True),
        'pos_order': fields.integer('Order', help='Order', required=True),
    }
    
    _defaults = {
        'signed_off': False,
    }                                         
    
class ng_state_payroll_stdconfig(models.Model):
    _name = "ng.state.payroll.stdconfig"
    _description = "Earnings & Deductions Configuration"

    _columns = {
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'initialized': fields.boolean('Initialized', help='Earnings & Deductions Initialized', required=True, readonly=1),
    } 
    
    _defaults = {
        'name': 'Basic Configuration',
        'initialized': True,
    } 
       
    def try_init_earn_dedt(self, cr, uid, context=None):
        _logger.info("Running try_init_earn_dedt: earnings/deductions cron-job...")
        stdconfig_singleton = self.pool.get('ng.state.payroll.stdconfig')
        stdconfig_ids = stdconfig_singleton.search(cr, uid, [('active', '=', True)], limit=1, context=context)
        if len(stdconfig_ids) == 1:
            stdconfig_obj = stdconfig_singleton.browse(cr, uid, stdconfig_ids[0], context=context)
            if not stdconfig_obj.initialized:
                _logger.info("Initializing earnings/deductions...")
                cr.execute("truncate rel_employee_std_earning")
                _logger.info("Truncated rel_employee_std_earning.")
                cr.execute("truncate rel_employee_std_deduction")
                _logger.info("Truncated rel_employee_std_deduction.")
                cr.execute("update hr_employee set resolved_earn_dedt='f'")
                _logger.info("Updated employee resolved_earn_dedt.")
                stdconfig_obj.init_earnings_deductions(context=context)
                stdconfig_obj.update({'initialized': True})
                _logger.info("Done initializing.")
        
        return True
                             
    @api.multi
    def init_earnings_deductions(self, context=None):
        employees = self.env['hr.employee'].search([('resolved_earn_dedt', '=', False), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
        _logger.info("init_earnings_deductions - Number of employees found: %d", len(employees))        
        
        tic = time.time()
        self.env.cr.execute('prepare insert_employee_std_earning (int, int) as insert into rel_employee_std_earning (employee_id,earning_id) values ($1, $2)')            
        self.env.cr.execute('prepare insert_employee_std_deduction (int, int) as insert into rel_employee_std_deduction (employee_id,deduction_id) values ($1, $2)')            
        for emp in employees:
            standard_earnings = self.env['ng.state.payroll.earning.standard'].search([('active', '=', True), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])            
            for e in standard_earnings:
                self.env.cr.execute('execute insert_employee_std_earning(%s,%s)', (emp.id,e.id))
                
            standard_deductions = self.env['ng.state.payroll.deduction.standard'].search([('active', '=', True), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])
            for d in standard_deductions:
                self.env.cr.execute('execute insert_employee_std_deduction(%s,%s)', (emp.id,d.id))            
        self.env.cr.execute("update hr_employee set resolved_earn_dedt='t'")
        self.env.cr.commit()
        _logger.info("Processed %d employees in %f seconds.", len(employees), (time.time() - tic))
    
    def try_resolve_earn_dedt(self, cr, uid, context=None):
        _logger.info("Running try_resolve_earn_dedt: earnings/deductions cron-job...")
        stdconfig_singleton = self.pool.get('ng.state.payroll.stdconfig')
        payroll_ids = stdconfig_singleton.search(cr, uid, [('active', '=', True)], limit=1, context=context)
        if len(payroll_ids) == 1:
            stdconfig_obj = stdconfig_singleton.browse(cr, uid, payroll_ids[0], context=context)
            stdconfig_obj.resolve_earnings_deductions(context=context)
        
        return True
                             
    @api.multi
    def resolve_earnings_deductions(self, context=None):
        employees = self.env['hr.employee'].search([('resolved_earn_dedt', '=', False), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
        _logger.info("resolve_earnings_deductions - Number of employees found: %d", len(employees))        
        
        tic = time.time()            
        for emp in employees:
            emp.standard_earnings.unlink()
            emp.standard_deductions.unlink()
            standard_earnings = self.env['ng.state.payroll.earning.standard'].search([('active', '=', True), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])
            standard_deductions = self.env['ng.state.payroll.deduction.standard'].search([('active', '=', True), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])
            emp.update({'resolved_earn_dedt': True})
            emp.update({'standard_earnings': standard_earnings})
            emp.update({'standard_deductions': standard_deductions})
        _logger.info("Processed %d employees in %f seconds.", len(employees), (time.time() - tic))
                        
class ng_state_payroll_scenario(models.Model):
    '''
    Scenario
    '''
    _name = "ng.state.payroll.scenario"
    _description = 'Scenario'

    _columns = {
        'name': fields.char('Name', help='Scenario Name', required=True),
        'total_amount': fields.float('Total Payroll Paid Amount', help='Total Payroll Paid Amount'),
        'total_amount_pension': fields.float('Total Pension Paid Amount', help='Total Pension Paid Amount'),
        'processing_time': fields.float('Processing Time', help='Processing Time'),
        'batch_id': fields.many2one('ng.state.payroll.scenariobatch', 'Scenario Batch'),
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll', required=True),
        'scenario_item_ids': fields.one2many('ng.state.payroll.scenario.item','scenario_id','Payroll Scenario Items', default=lambda self: self._default_scenario_item_ids()),
        'scenario2_item_ids': fields.one2many('ng.state.payroll.scenario2.item','scenario_id','Pension Scenario Items', default=lambda self: self._default_scenario2_item_ids()),
        'payment_ids': fields.one2many('ng.state.payroll.scenario.payment','scenario_id','Payroll Payment Items'),
        'payment2_ids': fields.one2many('ng.state.payroll.scenario2.payment','scenario_id','Pension Payment Items'),
        'signoff_ids': fields.one2many('ng.state.payroll.scenario.signoff','scenario_id','Sign-Off Items'),
        'signoff_pos_order': fields.integer('Sign-off Index', help='Sign-off Index'),
        'do_dry_run': fields.boolean('Dry Run', help='Tick check-box to do dry run'),
        'gov_sign': fields.binary(string='Governor Signature'),
        'ps_finance_sign': fields.binary(string='PS Finance Signature'),
        'state': fields.selection([
            ('draft','Draft'),
            ('in_progress','Processing'),
            ('processed','Processed'),
            ('closed','Closed'),
        ], 'Status')
    }

    _defaults = {
        'state': 'draft',
        'signoff_pos_order': 0,
    }

    @api.model
    def _default_scenario_item_ids(self):
        scenario_item_list = []
        scenario_item1 = {
            'level_min': 0,
            'level_max': 7,
            'percentage': 100,
        }
        scenario_item2 = {
            'level_min': 8,
            'level_max': 10000,
            'percentage': 50,
        }
        scenario_item_list.append(scenario_item1)
        scenario_item_list.append(scenario_item2)
        return scenario_item_list

    @api.model
    def _default_scenario2_item_ids(self):
        scenario2_item_list = []
        scenario2_item1 = {
            'amount_min': 0,
            'amount_max': 20000,
            'percentage': 100,
        }
        scenario2_item2 = {
            'amount_min': 20000.01,
            'amount_max': 99999999,
            'amount_max': 50,
        }
        scenario2_item_list.append(scenario2_item1)
        scenario2_item_list.append(scenario2_item2)
        return scenario2_item_list

    @api.model
    def revert(self, vals):
        #if self.env.user.has_group('hr_payroll_nigerian_state.group_payroll_admin'):
        self.env.cr.execute("update ng_state_payroll_scenario set total_amount=0,processing_time=0,state='draft'")
        self.env.cr.execute("update ng_state_payroll_payroll_item set balance_income = x.balance_income + x.amount from (select employee_id,balance_income,amount from ng_state_payroll_scenario_payment) x where x.employee_id = ng_state_payroll_payroll_item.employee_id")        
        self.env.cr.execute("update ng_state_payroll_pension_item set balance_income = x.balance_income + x.amount from (select employee_id,balance_income,amount from ng_state_payroll_scenario2_payment) x where x.employee_id = ng_state_payroll_payroll_item.employee_id")        
        self.env.cr.execute("delete from ng_state_payroll_scenario_item where scenario_id=" + str(vals[0]))
        self.env.cr.execute("delete from ng_state_payroll_scenario2_item where scenario_id=" + str(vals[0]))
        self.env.cr.execute("delete from ng_state_payroll_scenario_payment where scenario_id=" + str(vals[0]))
        self.env.cr.execute("delete from ng_state_payroll_scenario_signoff where scenario_id=" + str(vals[0]))
        self.env.invalidate_all()
                                                                 
    #On create; iterate through levels and create new scenario items
    #Method to do dry run
    #Method to save
    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        res = super(ng_state_payroll_scenario, self).create(vals)
            
        return res

    @api.multi
    def write(self, vals):
        _logger.info("Calling write..vals = %s", vals)
        
        if ('do_dry_run' in vals and vals['do_dry_run']) and vals['state'] == 'draft':
            vals['state'] = 'processed'
        
        return super(ng_state_payroll_scenario,self).write(vals)
   
    @api.multi   
    def run_finalize(self):
        return self.finalize()
   
    @api.multi   
    def run_dry_run(self):
        return self.dry_run()
        
    @api.multi
    def sign_off(self):        
        _logger.info("Calling sign_off..state = %s", self.state)
        #TODO Set sign-off entry for current user to true
        group_payroll_officer = self.env['res.groups'].search([('name', '=', 'Payroll Officer')])
        group_admin = self.env['res.groups'].search([('name', '=', 'Configuration')])
        #if group_payroll_officer in self.env.user.groups_id or group_admin in self.env.user.groups_id:
        if True:
            #Iterate through sign-off users and if all signed off, set state='closed'
            signoff_count = 0
            for sign_off in self.signoff_ids:
                if sign_off.user_id.id == self.env.user.id:
                    self.update({'signoff_pos_order': (self.signoff_pos_order + 1)})
                    sign_off.update({'signed_off': True})
                if sign_off.signed_off:
                    signoff_count += 1
            if len(self.signoff_ids) == signoff_count:
                self.state = 'closed'
                self.update({'state': 'closed'})        
   
    @api.multi
    def set_in_progress(self):
        self.write({'state': 'in_progress'})
        
    @api.onchange('do_dry_run')
    def dry_run(self):
        _logger.info("Calling dry_run...state = %s", self.state)        
        if self.state == 'in_progress':
            raise osv.except_osv(_('Info'), _('Processing already in progress.'))

        if not self.state == 'in_progress':        
            self.set_in_progress()            
            #Payment for payroll
            payroll_items = self.payroll_id.payroll_item_ids
            total_amount = 0
            payment_item_list = []        
            if self.payroll_id.total_balance_payroll > 0:
                for payroll_item in payroll_items:
                    if payroll_item.balance_income > 0:
                        scenario_item = False
                        for s_item in self.scenario_item_ids:
                            if payroll_item.employee_id.grade_level >= s_item.level_min and payroll_item.employee_id.grade_level <= s_item.level_max:
                                scenario_item = s_item
                                break
                        if scenario_item:
                            #Calculate the amount to be paid as a percentage of the Net
                            #If the amount is greater than the balance, pay the entire balance
                            amount = scenario_item.percentage * payroll_item.net_income / 100
                            if amount > payroll_item.balance_income:
                                amount = payroll_item.balance_income
                            total_amount += amount
                            payment_item = {
                                'employee_id': payroll_item.employee_id.id,
                                'active': True,
                                'amount': amount,
                                'payroll_item_id': payroll_item.id,
                                'balance_income': payroll_item.balance_income - amount,
                                'net_income': payroll_item.net_income,
                                'percentage': scenario_item.percentage,
                                'scenario_id': self.id
                            }
                            payment_item_list.append(payment_item)
                            payroll_item.update({'balance_income':payroll_item.balance_income - amount})
                self.total_amount = total_amount
                self.payment_ids = payment_item_list
    
            #Payment for pension
            pension_items = self.payroll_id.pension_item_ids
            total_amount = 0
            payment_item_list = []        
            if self.payroll_id.total_balance_pension > 0:
                for pension_item in pension_items:
                    if pension_item.balance_income > 0:
                        scenario2_item = False
                        for s_item in self.scenario2_item_ids:
                            if (pension_item.employee_id.annual_pension / 12) >= s_item.amount_min and (payroll_item.employee_id.annual_pension / 12) <= s_item.amount_max:
                                scenario2_item = s_item
                        if scenario2_item:
                            #Calculate the amount to be paid as a percentage of the Net
                            #If the amount is greater than the balance, pay the entire balance
                            amount = scenario2_item.percentage * (pension_item.employee_id.annual_pension / 12) / 100
                            if amount > pension_item.balance_income:
                                amount = pension_item.balance_income
                            total_amount += amount
                            payment_item = {
                                'employee_id': pension_item.employee_id.id,
                                'active': True,
                                'amount': amount,
                                'pension_item_id': pension_item.id,
                                'balance_income': pension_item.balance_income - amount,
                                'net_income': pension_item.net_income,
                                'percentage': scenario_item.percentage,
                                'scenario_id': self.id
                            }
                            payment_item_list.append(payment_item)
                            pension_item.update({'balance_income':payment_item.balance_income - amount})
                self.total_amount_pension = total_amount
                self.payment2_ids = payment_item_list

    @api.multi
    def finalize(self):
        _logger.info("Calling finalize...state = %s", self.state)
        if self.state == 'in_progress':
            raise osv.except_osv(_('Info'), _('Processing already in progress.'))
        
        if not self.state == 'in_progress':        
            self.set_in_progress()             
    
            #Payment for payroll
            payroll_items = self.payroll_id.payroll_item_ids
            total_amount = 0
            if self.payroll_id.total_balance_payroll > 0:
                for payroll_item in payroll_items:
                    if payroll_item.balance_income > 0:
                        scenario_item = False
                        for s_item in self.scenario_item_ids:
                            if payroll_item.employee_id.grade_level >= s_item.level_min and payroll_item.employee_id.grade_level <= s_item.level_max:
                                scenario_item = s_item
                        if scenario_item:
                            #Calculate the amount to be paid as a percentage of the Net
                            #If the amount is greater than the balance, pay the entire balance
                            amount = scenario_item.percentage * payroll_item.net_income / 100
                            if amount > payroll_item.balance_income:
                                amount = payroll_item.balance_income
                            total_amount += amount
                            payment_item = {'employee_id': payroll_item.employee_id.id,
                                                'active': True,
                                                'amount': amount,
                                                'payroll_item_id': payroll_item.id,
                                                'balance_income': payroll_item.balance_income - amount,
                                                'net_income': payroll_item.net_income,
                                                'percentage': scenario_item.percentage,
                                                'scenario_id': self.id}
                            self.env['ng.state.payroll.scenario.payment'].create(payment_item)
                            payroll_item.write({'balance_income':payroll_item.balance_income - amount})
                self.payroll_id.write({'total_balance_payroll': self.payroll_id.total_balance_payroll - amount})
                self.write({'state':'processed','total_amount':total_amount})
    
            #Payment for pension
            pension_items = self.payroll_id.pension_item_ids
            total_amount = 0
            if self.payroll_id.total_balance_pension > 0:
                for pension_item in pension_items:
                    if pension_item.balance_income > 0:
                        scenario2_item = False
                        for s_item in self.scenario2_item_ids:
                            if (pension_item.employee_id.annual_pension / 12) >= s_item.amount_min and (payroll_item.employee_id.annual_pension / 12) <= s_item.amount_max:
                                scenario2_item = s_item
                        if scenario2_item:
                            #Calculate the amount to be paid as a percentage of the Net
                            #If the amount is greater than the balance, pay the entire balance
                            amount = scenario2_item.percentage * (pension_item.employee_id.annual_pension / 12) / 100
                            if amount > pension_item.balance_income:
                                amount = pension_item.balance_income
                            total_amount += amount
                            payment_item = {'employee_id': pension_item.employee_id.id,
                                                'active': True,
                                                'amount': amount,
                                                'pension_item_id': pension_item.id,
                                                'balance_income': pension_item.balance_income - amount,
                                                'net_income': pension_item.net_income,
                                                'percentage': scenario_item.percentage,
                                                'scenario_id': self.id}
                            self.env['ng.state.payroll.scenario2.payment'].create(payment_item)
                            pension_item.write({'balance_income':payment_item.balance_income - amount})
                self.payroll_id.write({'total_balance_pension': self.payroll_id.total_balance_pension - amount})
                self.write({'state':'processed','total_amount_pension':total_amount})

class ng_state_payroll_scenario_item(models.Model):
    '''
    Payroll Scenario Item
    '''
    _name = "ng.state.payroll.scenario.item"
    _description = 'Payroll Scenario Item'

    _columns = {
        'percentage': fields.float('Percentage', help='Percentage', default=100),
        'level_min': fields.integer('Minimum Level', help='Minimum Level'),
        'level_max': fields.integer('Maximum Level', help='Maximum Level'),
        'scenario_id': fields.many2one('ng.state.payroll.scenario', 'Scenario'),
    }
    
class ng_state_payroll_scenario2_item(models.Model):
    '''
    Pension Scenario Item
    '''
    _name = "ng.state.payroll.scenario2.item"
    _description = 'Pension Scenario Item'

    _columns = {
        'percentage': fields.float('Percentage', help='Percentage', default=100),
        'amount_min': fields.float('Minimum Amount', help='Minimum Amount'),
        'amount_max': fields.float('Maximum Amount', help='Maximum Amount'),
        'scenario_id': fields.many2one('ng.state.payroll.scenario', 'Scenario'),
    }
    
class ng_state_payroll_payroll_summary(models.Model):
    '''
    Summary Item
    '''
    _name = "ng.state.payroll.payroll.summary"
    _description = 'Summary Item'

    _columns = {
        'department_id': fields.many2one('hr.department', 'MDA', required=True),
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll'),
        'total_taxable_income': fields.float('Taxable', help='Total Taxable Income'),
        'total_gross_income': fields.float('Gross', help='Total Gross Income'),
        'total_net_income': fields.float('Net', help='Total Net Income'),
        'total_paye_tax': fields.float('Tax', help='Total PAYE Tax'),
        'total_leave_allowance': fields.float('Leave All.', help='Leave Allowance'),
    }
    
    _defaults = {
        'total_gross_income': 0,
        'total_taxable_income': 0,
        'total_net_income': 0,
        'total_paye_tax': 0,
        'active': True,
        'resolve': False,
    }                                          

class ng_state_payroll_subvention_item(models.Model):
    '''
    Subvention Item
    '''
    _name = "ng.state.payroll.subvention.item"
    _description = 'Subvention Item'

    _columns = {
        'department_id': fields.many2one('hr.department', 'MDA', required=True),
        'name': fields.char('Name', help='Earning Name', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'amount': fields.float('Amount', help='Amount', required=True),
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll'),
    }
    
    _defaults = {
        'amount': 0,
        'active': True,
    }                                          

class ng_state_payroll_scenario_payment(models.Model):
    '''
    Payroll Payment Item
    '''
    _name = "ng.state.payroll.scenario.payment"
    _description = 'Payment Item'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'net_income': fields.float('Net Income', help='Net Income for calendar period', required=True),
        'balance_income': fields.float('Payment Balance', help='Balance of paid income for calendar period', required=True),
        'amount': fields.float('Paid Amount', help='Amount paid out of expected Net', required=True),
        'percentage': fields.float('Percentage', help='Percentage of Net Salary Paid', required=True),
        'payroll_item_id': fields.many2one('ng.state.payroll.payroll.item', 'Payroll Item', required=True),
        'scenario_id': fields.many2one('ng.state.payroll.scenario', 'Scenario', required=True),
    }
    
    _defaults = {
        'amount': 0,
        'percentage': 0,
        'active': True,
    }                                          

class ng_state_payroll_scenario2_payment(models.Model):
    '''
    Payment Item
    '''
    _name = "ng.state.payroll.scenario2.payment"
    _description = 'Pension Payment Item'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'net_income': fields.float('Net Income', help='Net Income for calendar period', required=True),
        'balance_income': fields.float('Payment Balance', help='Balance of paid income for calendar period', required=True),
        'amount': fields.float('Paid Amount', help='Amount paid out of expected Net', required=True),
        'percentage': fields.float('Percentage', help='Percentage of Net Salary Paid', required=True),
        'pension_item_id': fields.many2one('ng.state.payroll.payroll.item', 'Payroll Item', required=True),
        'scenario_id': fields.many2one('ng.state.payroll.scenario', 'Scenario', required=True),
    }
    
    _defaults = {
        'amount': 0,
        'percentage': 0,
        'active': True,
    }                                          

class ng_state_payroll_pension_item(models.Model):
    '''
    Pension Item
    '''
    _name = "ng.state.payroll.pension.item"
    _description = 'Pension Item'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'payment_item_ids': fields.one2many('ng.state.payroll.scenario2.payment','scenario_id','Payment Items', compute='_compute_payment_items'),
        'gross_income': fields.float('Gross', help='Gross Income'),
        'net_income': fields.float('Net', help='Net Income'),
        'balance_income': fields.float('Unpaid', help='Unpaid Balance'),
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll'),
        'item_line_ids': fields.one2many('ng.state.payroll.pension.item.line','item_line_id','Pension Item Lines'),
    }
    
    _defaults = {
        'gross_income': 0,
        'net_income': 0,
        'active': True,
    }        
   
    @api.depends('payroll_id', 'employee_id')   
    def _compute_payment_items(self):
        for payroll_item in self:
            payroll_item.payment_item_ids = self.env['ng.state.payroll.scenario2.payment'].search([('employee_id.id', '=', payroll_item.employee_id.id), ('scenario_id.payroll_id.id', '=', payroll_item.payroll_id.id)])        
    
class ng_state_payroll_payroll_item(models.Model):
    '''
    Payroll Item
    '''
    _name = "ng.state.payroll.payroll.item"
    _description = 'Payroll Item'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'active': fields.boolean('Active', help='Active Status', required=True),
        'resolve': fields.boolean('Resolve', help='Requires Resolution'),
        'retiring': fields.boolean('Retiring', help='Retiring this calendar period'),
        'payment_item_ids': fields.one2many('ng.state.payroll.scenario.payment','scenario_id','Payment Items', compute='_compute_payment_items'),
        'item_line_ids': fields.one2many('ng.state.payroll.payroll.item.line','item_line_id','Payroll Item Lines'),
        'taxable_income': fields.float('Taxable', help='Taxable Income'),
        'gross_income': fields.float('Gross', help='Gross Income'),
        'net_income': fields.float('Net', help='Net Income'),
        'leave_allowance': fields.float('Leave Allowance', help='Leave Allowance'),
        'balance_income': fields.float('Unpaid', help='Unpaid Balance'),
        'paye_tax': fields.float('Tax', help='PAYE Tax'),
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll'),
    }
    
    _defaults = {
        'gross_income': 0,
        'taxable_income': 0,
        'net_income': 0,
        'leave_allowance': 0,
        'paye_tax': 0,
        'active': True,
        'resolve': False,
        'retiring': False,
    }                                          
   
    @api.depends('payroll_id', 'employee_id')   
    def _compute_payment_items(self):
        for payroll_item in self:
            payroll_item.payment_item_ids = self.env['ng.state.payroll.scenario.payment'].search([('employee_id.id', '=', payroll_item.employee_id.id), ('scenario_id.payroll_id.id', '=', payroll_item.payroll_id.id)])        
                        
class ng_state_payroll_payroll_item_line(models.Model):
    '''
    Payroll Item Line
    '''
    _name = "ng.state.payroll.payroll.item.line"
    _description = 'Payroll Item Line'

    _columns = {
        'code': fields.char('Code', help='Line Code', required=False),
        'name': fields.char('Name', help='Line Name', required=False),
        'amount': fields.float('Amount', help='Amount', required=True),
        'item_line_id': fields.many2one('ng.state.payroll.payroll.item', 'Payroll Item'),
    }
                        
class ng_state_payroll_pension_item_line(models.Model):
    '''
    Pension Item Line
    '''
    _name = "ng.state.payroll.pension.item.line"
    _description = 'Pension Item Line'

    _columns = {
        'code': fields.char('Code', help='Line Code', required=False),
        'name': fields.char('Name', help='Line Name', required=False),
        'amount': fields.float('Amount', help='Amount', required=True),
        'item_line_id': fields.many2one('ng.state.payroll.pension.item', 'Pension Item'),
    }
    
class ng_state_payroll_payroll_signoff(models.Model):
    '''
    Payroll Sign-Off
    '''
    _name = "ng.state.payroll.payroll.signoff"
    _description = 'Payroll Sign-Off'

    _columns = {
        'payroll_id': fields.many2one('ng.state.payroll.payroll', 'Payroll', required=True),
        'user_id': fields.many2one('res.users', 'Payroll Officer', required=True, domain="[('groups_id.name','=','Payroll Officer')]"),
        'signed_off': fields.boolean('Closed', help='Sign-Off closed status', required=True),
        'pos_order': fields.integer('Order', help='Order', required=True),
    }
    
    _defaults = {
        'signed_off': False,
    }                                          

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for r in self.read(cr, uid, ids, ['id', 'payroll_id', 'user_id'], context):
            aux = " ("
            if r['payroll_id']:
                aux += r['payroll_id'][1]
                # why translate a date? I think is a mistake, the _() function must have a 
                # known string, example _("the start date is %s") % r['from_date']
    
            aux +=  ' - '
            if r['user_id']:
                aux += r['user_id'][1] # same question
    
            aux += ')'
    
            # aux is the name items for the r['id']
            res.append((r['id'], aux))  # append add the tuple (r['id'], aux) in the list res
    
        return res
        #Open create form with current month date range
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('id','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('payroll_id',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('user_id',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                    #End
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('id','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
            
class ng_state_payroll_payroll(models.Model):
    '''
    Payroll
    '''
    _name = "ng.state.payroll.payroll"
    _description = 'Payroll'

    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _columns = {
        'name': fields.char('Name', help='Payroll Name', required=True),
        'calendar_id': fields.many2one('ng.state.payroll.calendar', 'Calendar', track_visibility='onchange', required=True),
        'total_net_payroll': fields.float('Payroll Total Net', help='Payroll Total Net'),
        'total_gross_payroll': fields.float('Payroll Total Gross', help='Payroll Total Gross'),
        'total_taxable_payroll': fields.float('Payroll Total Net', help='Payroll Total Taxable'),
        'total_tax_payroll': fields.float('Payroll Total Tax', help='Payroll Total Tax'),
        'total_balance_payroll': fields.float('Payroll Total Balance', help='Total Balance Payroll Payment'),
        'total_net_pension': fields.float('Pension Total Net', help='Pension Total Net'),
        'total_gross_pension': fields.float('Pension Total Gross', help='Pension Total Gross'),
        'total_balance_pension': fields.float('Pension Total Balance', help='Total Balance Pension Payment'),
        'processing_time_payroll': fields.float('Payroll Processing Time', help='Payroll Processing Time'),
        'processing_time_pension': fields.float('Pension Processing Time', help='Pension Processing Time'),
        'notify_emails': fields.char('Notify Email', help='Comma separated email recipients for event notification', required=False),
        'from_date': fields.related('calendar_id', 'from_date', string='From Date', readonly=1),
        'to_date': fields.related('calendar_id', 'to_date', string='To Date', readonly=1),
        'payroll_item_ids': fields.one2many('ng.state.payroll.payroll.item','payroll_id','Payroll Items'),
        'pension_item_ids': fields.one2many('ng.state.payroll.pension.item','payroll_id','Pension Items'),
        'subvention_item_ids': fields.one2many('ng.state.payroll.subvention.item','payroll_id','Subvention Items'),
        'payroll_summary_ids': fields.one2many('ng.state.payroll.payroll.summary','payroll_id','Payroll Summary Items'),
        'signoff_ids': fields.one2many('ng.state.payroll.payroll.signoff','payroll_id','Sign-Off Items'),
        'signoff_pos_order': fields.integer('Sign-off Index', help='Sign-off Index'),
        'scenario_ids': fields.one2many('ng.state.payroll.scenario','payroll_id','Scenario Payments'),       
        'do_dry_run': fields.boolean('Dry Run', help='Tick check-box to do dry run'),
        'auto_process': fields.boolean('Auto-process', help='Tick check-box for automatic processing'),
        'in_progress': fields.boolean('In Progress', help='Indicates processing currently in progress'),
        'do_payroll': fields.boolean('Run Payroll', help='Tick check-box to run active employee payroll'),
        'do_pension': fields.boolean('Run Pension', help='Tick check-box to run pension payroll'),
        'gov_sign': fields.binary('Governor Signature'),
        'ps_finance_sign': fields.binary('PS Finance Signature'),
        'state': fields.selection([
            ('draft','Draft'),
            ('pending','Pending'),
            ('in_progress','Processing'),
            ('processed','Processed'),
            ('closed','Closed'),
        ], 'Status')
    }
    
    _defaults = {
        'state': 'draft',
        'signoff_pos_order': 0,
        'do_dry_run': False,
        'auto_process': True,
    }                                          

    _track = {
        'state': {
            'ng_state_payroll_payroll.mt_alert_promo_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_payroll.mt_alert_promo_in_progress':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'in_progress',
            'ng_state_payroll_payroll.mt_alert_promo_processed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'processed',
            'ng_state_payroll_payroll.mt_alert_promo_closed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'closed',
        },
    }
    
    @api.depends('signoff_ids')
    def _check_user_signer(self):
        _logger.info("Calling _check_user_signer..state = %s", self.state)
        self.current_user_signer = False
        #if self.env.user.groups_id.name == 'Payroll Officer':
        #    for sign_off in self.signoff_ids:
        #        if sign_off.user_id.id == self.env.user.id:
        #            self.current_user_signer = True
        #            break
   
    @api.multi
    def run_dry_run(self, vals):
        return self.dry_run()
        
    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        if not vals['auto_process']:
            vals['state'] = 'in_progress'
        res = super(ng_state_payroll_payroll, self).create(vals)
        
        return res

    @api.multi
    def write(self, vals):
        _logger.info("Calling write..vals = %s", vals)
     
        return super(ng_state_payroll_payroll,self).write(vals)

    @api.model
    def revert(self, vals):
        _logger.info("Calling revert..vals = %s", vals)
        #if self.env.user.has_group('hr_payroll_nigerian_state.group_payroll_admin'):
        if self.do_payroll:
            self.env.cr.execute("update ng_state_payroll_payroll set total_tax_payroll=0,total_net_payroll=0,total_gross_payroll=0,total_taxable_payroll=0,total_balance_payroll=0,processing_time_payroll=0,state='draft' where id=" + str(vals[0]))
            self.env.cr.execute("delete from ng_state_payroll_payroll_item where payroll_id=" + str(vals[0]))
            self.env.cr.execute("delete from ng_state_payroll_payroll_item_line where item_line_id=null")
            self.env.cr.execute("delete from ng_state_payroll_payroll_summary where payroll_id=" + str(vals[0]))
            self.env.invalidate_all()
        
        if self.do_pension:
            self.env.cr.execute("update ng_state_payroll_payroll set total_net_pension=0,total_gross_pension=0,total_balance_pension=0,processing_time_pension=0,state='draft' where id=" + str(vals[0]))
            self.env.cr.execute("delete from ng_state_payroll_pension_item where payroll_id=" + str(vals[0]))
            self.env.cr.execute("delete from ng_state_payroll_pension_item_line where item_line_id=null")
            self.env.invalidate_all()
        
    @api.multi
    def sign_off(self):        
        _logger.info("Calling sign_off..state = %s", self.state)
        #TODO Set sign-off entry for current user to true
        group_payroll_officer = self.env['res.groups'].search([('name', '=', 'Payroll Officer')])
        group_admin = self.env['res.groups'].search([('name', '=', 'Configuration')])
        #if group_payroll_officer in self.env.user.groups_id or group_admin in self.env.user.groups_id:
        if True:
            #Iterate through sign-off users and if all signed off, set state='closed'
            signoff_count = 0
            for sign_off in self.signoff_ids:
                if sign_off.user_id.id == self.env.user.id:
                    self.update({'signoff_pos_order': (self.signoff_pos_order + 1)})
                    sign_off.update({'signed_off': True})
                if sign_off.signed_off:
                    signoff_count += 1
            if len(self.signoff_ids) == signoff_count:
                self.state = 'closed'
                self.update({'state': 'closed'})        
        #TODO if state_flag = 'closed delete all nonstandard deductions and earnings for the payroll calendar period
          
    @api.multi
    def set_pending(self, context=None):
        _logger.info("Calling set_pending...")
        
        self.write({'state': 'pending'})
        return True   
    
    @api.multi
    def set_in_progress(self, context=None):
        _logger.info("Calling set_in_progress...")
        
        self.write({'state': 'in_progress'})
        return True   
    
    @api.multi
    def set_finalized(self, context=None):
        _logger.info("Calling set_finalized...")
        
        self.write({'state': 'processed'})
        return True   
    
    def try_finalize(self, cr, uid, context=None):
        _logger.info("Running payroll cron-job...")
        payroll_singleton = self.pool.get('ng.state.payroll.payroll')
        payroll_ids = payroll_singleton.search(cr, uid, [('state', '=', 'pending'),('auto_process', '=', True)], context=context)
        payroll_obj = None
        for payroll_id in payroll_ids:
            payroll_obj = payroll_singleton.browse(cr, uid, payroll_id, context=context)
            payroll_obj.set_in_progress(context=context)
            payroll_obj.finalize(context=context)

        return True
                        
    @api.multi
    def exec_finalize(self, context=None):
        self.set_in_progress(context=context)
        self.finalize(context=context)
                        
    @api.multi
    def finalize(self, context=None):
        _logger.info("Calling finalize...state = %s", self.state)
        
        if self.state == 'in_progress':
            if self.calendar_id:
                if self.do_payroll:
                    tic = time.time()
                    #item_list = []
                            
                    #List all subvention earnings for this calendar period
                    subventions = self.env['ng.state.payroll.subvention'].search([('active', '=', True), ('calendar_id', '=', self.calendar_id.id)])
            
                    #List all tax rules
                    paye_taxrules = self.env['ng.state.payroll.taxrule'].search([('active', '=', True)])
                    
                    #Fetch all active employees *TODO* (and non-suspended employees)
                    #employees = self.env['hr.employee'].search([('resolved_earn_dedt', '=', True), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
                    #employees = self.env['hr.employee'].search([('employee_no', 'in', ['30042','45735'])])
                    #employees = self.env['hr.employee'].search([('employee_no', 'in', ['46330'])])
                    employees = self.env['hr.employee'].search([('employee_no', 'in', ['46330','66134','66107','66178','66305','66290','66006','66316','66536','69624','36633','P0008235','29823','65891','38851','66597','65881','80023','80005','80038','46342','66644','46422','46409','66401','65902','65841','65911','46629','46712','46407','46384','46438','65837','46604','65830','66422','46553','65967','66192','66079','66233','66631','66725','66065','65898','66010','32928','36493','46684','35350','66636','69565','66432','0066633_D','8030','1191','5844','9406','5574','82717','6615','4276','14570','66723','183','4411','31517','17814','40014','82068','65957','66498','80617','46377','43388','40401','65684','43890','82554','83897','66701','38910','36498','29872','47146','75011','40049','31799','66414','42097','88397','66619','46396','38907','66618','3335','81555','6811','70056','46745','3361','47941','83927','43751','3362','3344','30176','83255','45157','41964','46762','83805','83915','66572','65743','30437','3341','3374','41164','38956','44720','44598','83778','38951','36792','47934','38991','58384','38982','58054','38927','41270','40962','45018','83137','83127','72822','43884','39563','44125','83158','70099','83249','47942','83721','74675','67593','78042','24582','30994','46731','43997','83274','74019','41365','83251','83128','83122','83101','43467','83107','83106','83098','41156','17554','83559','89720','34897','44958','39088','38717','75026','78587','74713','74710','74709','42641','83048','46612','38767','83164','83161','83097','83175','83121','44144','83124','83118','83237','83102','45685','83160','83119','83103','83134','83130','83123','83145','44934','83212','82429','83096','89718','43602','41576','83431','83276','82992','82826','86520','47874','83693','44500','83773','83605','44973','69805','83813','89748','83774','83911','34682','66488','83186','83156','35331','33450','83607','83162','83914','83125','83159','83238','83105','83099','3385','3330','83071','84895','83178','83140','89427','83218','89742','77399','79215','88591','86501','89683','83718','83187','83248','79078','29948','69389','73631','38740','30251','83043','83534','83042','43678','89429','83906','73461','83157','83132','83131','83117','83252','83250','31171','82308','72107','70545','89672','89404','89377','89374','89357','82276','889378','82180','82236','82593','82378','83433','83155','83092','83100','83536','83731','83421','83095','82375','89420','82104','89388','82386','82283','89643','89399','82657','82249','82238','82706','82643','82640','82630','82617','82543','82349','82343','82267','82265','82246','82666','89375','82715','82588','82548','82052','82597','82107','89641','89385','89383','89354','82685','82664','82661','82614','82596','82589','82393','82384','82278','82049','82594','82659','82652','82637','82635','82634','82611','82389','82237','82547','89372','82648','82553','82615','82295','89676','89675','89671','89670','89655','89654','89649','89647','89423','89419','89402','89395','89392','89380','89379','89373','89368','89367','84839','82721','82720','82719','82716','82714','82713','82711','82710','82709','82699','82662','82656','82649','82639','82638','82605','82600','82581','82580','82579','82573','82569','82552','82550','82546','82537','82390','82388','82383','82377','82376','82348','82347','82346','82345','82344','82342','82293','82292','82286','82285','82284','82277','82264','82263','82261','82256','82255','82253','82240','82108','82100','82043','89394','82536','89669','89376','89370','89369','82387','82331','82046','82048','82235','83624','82584','89644','89414','89408','89381','89352','89351','83621','82708','82234','89348','89424','89405','89391','82705','82658','82583','82566','82392','82385','82381','82242','82183','82044','82631','82047','89393','82647','82251','82551','89648','89396','89371','83636','82712','82660','82655','82601','82254','89382','82587','82280','89673','89652','89421','89413','89349','83637','83635','83633','83616','82718','82684','82651','82636','82616','82571','82544','82461','82391','82106','82045','89426','89418','89412','89390','83623','82686','82682','82619','82606','82586','82572','82340','82294','82289','82288','82274','82252','82250','82245','82244','82530','84893','84899','82535','81541','82290','82281','82053','82050','89406','82697','82243','82105','82665','82703','82700','82300','82299','82275','89411','89403','89384','82688','82683','82602','82287','89674','89658','89656','89651','89646','89638','89425','89417','89415','89410','89398','89397','89358','89350','83650','83634','83632','82707','82702','82701','82698','82663','82653','82650','82645','82633','82632','82613','82612','82599','82591','82585','82582','82570','82567','82545','82531','82411','82382','82380','82379','82374','82341','82338','82303','82282','82279','82257','82247','82233','82103','82102','82101','89356','82549','89642','89401','82646','78409','78322','78324','78323','78325','78326','35612','82298','79034','68871','78219','86028','28158','27388','27396','37146','34368','37511','P0028881','88796','86679','89022','74840','77206','41677','39311','41939','84646','31919','29928','58123','35917','86937','83890','83799','35637','89745','75349','83852','41059','31957','31689','41681','4432','39602','39938A','42285','41660','38591','41638','23101','40589','39278','39283','40092','41661','39153','41666','82949','58391','41450','46788','44756','74613','39860','3405','31880','18485','83825','32905','39595','28207','83803','45680','75014','44947','7629','0065686_D','39004','82094','39037','30445','34350','41624','38716','6001','3547','22505','12507','32342','41856','5431','31692','32101','38921','11369','11368','44493','3337','44097','20179','18551','82540','42118','44789','17798','11652','14867','42112','72911','87612','38885','38882','17928','41506','41187','40756','3342','9432','44675','17865','14567','4414','20924','32546','3410','3377','22560','4320','9420','9344','7238','1177','9365','9093','1427','17806','45757','12597','82590','15782','32286','20189','82302','6996','20916','20912','01726_D','44552','8909','3861','30801','16173','9175','21847','11730','13695','43940','4446','79555','2850','29478','20760','20925','22242','58694','72856','87613','35323','19911','30997','18737','27852','20579','21978','37449','30984','36320','33535','3697','5544','1417'])])

                    _logger.info("Count employees= %d", len(employees))        
                    
                    total_gross = 0
                    total_net = 0
                    total_tax = 0
                    total_taxable = 0
                    self.env.cr.execute('prepare insert_item (int,bool,int,numeric,numeric,numeric,numeric,numeric,numeric,bool,bool) as insert into ng_state_payroll_payroll_item (employee_id,active,payroll_id,gross_income,net_income,balance_income,taxable_income,paye_tax,leave_allowance,retiring,resolve) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) returning id')
                    self.env.cr.execute('prepare insert_item_line (int, text, numeric) as insert into ng_state_payroll_payroll_item_line (item_line_id,name,amount) values ($1, $2, $3) returning id')
                    dept_summary = {}
            
                    for emp in employees:
                        #TODO When an employee has been reinstated in this calendar period,- 
                        #pick all previously inactive payroll items from previous calendar- 
                        #periods from the suspension month to current calendar period, move-
                        #them to current pay period and set them active
                        _logger2.info("---------------------------------------------")
                        _logger2.info("Name=%s", emp.name_related)
                        #item_list_lines = []
                            
                        #Create Payroll Item and Payroll Item Lines
                        active_flag = 'f'
                        if emp.status_id.name == 'ACTIVE':
                            active_flag = 't'
                        #item_dict = {'employee_id':emp.id, 'active': active_flag, 'payroll_id': self.id}
                        item_line_income = 0
                        item_line_gross = 0
                        item_line_earnings_standard = 0
                        item_line_earnings_nonstd = 0
                        item_line_deductions_standard = 0
                        item_line_deductions_nonstd = 0
                        item_line_leave = 0
                        item_line_deduction = 0
                        item_line_relief = 0
                        item_line_income_ded = 0
                        
                        standard_earnings = emp.standard_earnings.filtered(lambda r: r.active == True)
                        standard_deductions = emp.standard_deductions.filtered(lambda r: r.active == True)
                        nonstd_earnings = emp.nonstd_earnings.filtered(lambda r: self.calendar_id in r.calendars and r.active == True)
                        nonstd_deductions = emp.nonstd_deductions.filtered(lambda r: self.calendar_id in r.calendars and r.active == True)
                        #Calculate each standard earning
                                                
                        basic_salary = False

                        for o in standard_earnings:
                            if o.name == 'BASIC SALARY':
                                basic_salary = o
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                amount = o.amount * o.derived_from.amount * 0.01
                            _logger2.info("Standard Earning[%s]=%f", o.name, amount)
                            item_line_gross += amount
                            item_line_earnings_standard += amount
                         
                        #Calculate each standard deduction
                        for o in standard_deductions:
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                if o.derived_from.fixed:
                                    amount = o.amount * o.derived_from.amount * 0.01
                                else:
                                    amount = o.amount * (o.derived_from.amount * 0.01 * o.derived_from.derived_from.amount) * 0.01
                            _logger2.info("Standard Deduction[%s]=%f", o.name, -amount)
                            item_line_deduction += amount
                            item_line_deductions_standard += amount
                            if o.income_deduction:
                                item_line_income_ded += amount
                                _logger2.info("Income Ded[%s]=%f", o.name, amount)                        
                            if o.relief:
                                item_line_relief += amount
                                _logger2.info("Relief[%s]=%f", o.name, amount)
                                
                        #Calculate each non-standard earning
                        for e in nonstd_earnings:
                            item_line_gross += (e.amount)
                            item_line_earnings_nonstd += (e.amount)
                            _logger2.info("Nonstandard Earning[%s]=%f" % (e.name, e.amount))
                
                        #Calculate each non-standard deduction
                        for d in nonstd_deductions:
                            _logger2.info("Nonstandard Deduction[%s]=%f", d.name, d.amount)
                            #TODO Create a configuration entity to manage reliefs
                            item_line_deduction += (d.amount * 12)
                            item_line_deductions_nonstd += (d.amount)
                            if d.income_deduction:
                                item_line_income_ded += (d.amount * 12)
                                _logger2.info("Income Ded[%s]=%f", d.name, d.amount)                        
                            if d.relief:
                                item_line_relief += (d.amount * 12)
                                _logger2.info("Relief[%s]=%f", d.name, d.amount)                        

                        item_id = False
                                
                        #Pro-rate for retiring employees
                        item_line_retiring = 'f'
                        #Use hire date and date of birth to calculate retirement date
                        retirement_date = False
                        retirement_date_dofa = False
                        retirement_date_dob = False
                        if emp.payscheme_id.use_dofa:
                            retirement_date_dofa = datetime.strptime(emp.hire_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(years=emp.payscheme_id.service_years)
                            retirement_date = retirement_date_dofa
                        if emp.payscheme_id.use_dob:
                            retirement_date_dob = datetime.strptime(emp.birthday, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(years=emp.payscheme_id.retirement_age)
                            retirement_date = retirement_date_dob
                        if emp.payscheme_id.use_dofa and emp.payscheme_id.use_dob:
                            if retirement_date_dofa < retirement_date_dob:
                                retirement_date = retirement_date_dofa
                            else:
                                retirement_date = retirement_date_dob
                                                
                        _logger2.info("Retirement Date=%s", retirement_date)
                        _logger2.info("Retirement Date DOFA=%s", retirement_date_dofa)
                        _logger2.info("Retirement Date DOB=%s", retirement_date_dob)
       
                        if retirement_date:
                            pay_month = datetime.strptime(self.calendar_id.from_date, '%Y-%m-%d').strftime('%m')
                            pay_year = datetime.strptime(self.calendar_id.from_date, '%Y-%m-%d').strftime('%Y')
                            if retirement_date.month == pay_month and retirement_date.year == pay_year:
                                item_line_retiring = 't'
                                retirement_day = datetime.strptime(emp.retirement_due_date, '%Y-%m-%d').strftime('%d')
                                item_line_gross *= (float(retirement_day) / 30.0)
                                _logger2.info("Pro-rated Gross=%f", item_line_gross)
                                #item_line_taxable *= (float(retirement_day) / 30)
                                
                        #Pay Leave Allowance for employees on birthdays that fall in this pay calendar
                        #Add Leave allowance to taxable and gross income
                        item_line_leave = 0
                        item_line_income = item_line_gross
                        leave_allowance = self.env['ng.state.payroll.leaveallowance'].search([('payscheme_id', '=', emp.payscheme_id.id)])
                        #if not leave_allowance:
                            #leave_allowance = self.env['ng.state.payroll.leaveallowance'].create({'payscheme_id':emp.payscheme_id.id,'percentage':10})
                        if leave_allowance and basic_salary:
                            item_line_leave = basic_salary.amount * leave_allowance.percentage / 100
                            item_line_income += item_line_leave
                            _logger2.info("Leave Allowance=%f", item_line_leave)
                                    
                        #Calculate PAYE Tax for each employee based on each taxable income items.
                        #Reduce Annual Income by Party Deduction to calculate CRA 20%
                        item_line_relief += ((item_line_income - item_line_income_ded) * 0.2 + 200000) #CRA relief
                        item_line_taxable = item_line_income - item_line_relief
                        total_taxable += (item_line_taxable / 12)
                        item_line_tax = 0
                        prev_to_amount = 0
                        if item_line_taxable < 0:
                            item_line_taxable = 0
                        for taxrule in paye_taxrules:
                            if item_line_taxable - taxrule.to_amount >= 0:
                                item_line_tax += ((taxrule.percentage / 100) * (taxrule.to_amount - prev_to_amount))
                                _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (taxrule.to_amount - prev_to_amount), taxrule.percentage, item_line_tax)
                                prev_to_amount = taxrule.to_amount
                            else:
                                item_line_tax += ((taxrule.percentage / 100) * (item_line_taxable - prev_to_amount))
                                _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (item_line_taxable - prev_to_amount), taxrule.percentage, item_line_tax)
                                break
                       
                        #Apply 1% PAYE rule
                        tax_1percent = item_line_income * 0.01
                        if item_line_tax < tax_1percent:
                            item_line_tax = tax_1percent                        
                        
                        item_line_net = item_line_gross - item_line_deduction - item_line_tax
                        
                        monthly_gross = item_line_earnings_nonstd + item_line_earnings_standard / 12
                        monthly_deductions = item_line_deductions_nonstd + item_line_deductions_standard / 12
                        monthly_net = monthly_gross - monthly_deductions - item_line_tax / 12
                        
                        _logger2.info("Annual Income=%f", item_line_income)
                        _logger2.info("Annual Gross=%f", item_line_gross)
                        _logger2.info("Monthly Gross=%f", monthly_gross)
                        _logger2.info("Annual Net=%f", item_line_net)
                        _logger2.info("Monthly Net=%f", monthly_net)
                        _logger2.info("Annual Relief=%f", item_line_relief)
                        _logger2.info("Annual Taxable=%f", item_line_taxable)
                        _logger2.info("Annual PAYE=%f", item_line_tax)
                        
                        if monthly_gross > 0:
                            total_gross = total_gross + monthly_net
                            total_net = total_net + monthly_net
                            if item_line_tax > 0:
                                total_tax = total_tax + (item_line_tax / 12)
                                
                            self.env.cr.execute('execute insert_item(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (emp.id,active_flag,self.id,monthly_gross,monthly_net,monthly_net,(item_line_taxable / 12),(item_line_tax / 12),item_line_leave,item_line_retiring,'f'))
                            item_id = self.env.cr.fetchone()
            
                            if not dept_summary.has_key(emp.department_id.id):
                                dept_summary[emp.department_id.id] = {'department_id':emp.department_id.id,'payroll_id':self.id,'total_taxable_income':0,'total_gross_income':0,'total_net_income':0,'total_paye_tax':0,'total_leave_allowance':0}
                            else:
                                dept_summary[emp.department_id.id]['total_taxable_income'] += (item_line_taxable / 12)
                                dept_summary[emp.department_id.id]['total_gross_income'] += monthly_gross
                                dept_summary[emp.department_id.id]['total_net_income'] += (item_line_net / 12)
                                dept_summary[emp.department_id.id]['total_paye_tax'] += (item_line_tax / 12)
                                dept_summary[emp.department_id.id]['total_leave_allowance'] += item_line_leave
                        else:
                            self.env.cr.execute('execute insert_item(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (emp.id,active_flag,self.id,0,0,0,0,0,0,'f','t'))
                            item_id = self.env.cr.fetchone()
                        
                        if item_id:
                            #Calculate each standard earning
                            for o in standard_earnings:
                                amount = 0
                                if o.fixed:
                                    amount = o.amount
                                else:
                                    amount = o.amount * o.derived_from.amount * 0.01
                                self.env.cr.execute('execute insert_item_line(%s,%s,%s)', (item_id[0],o.name,amount))
                             
                            for o in standard_deductions:
                                amount = 0
                                if o.fixed:
                                    amount = o.amount
                                else:
                                    if o.derived_from.fixed:
                                        amount = o.amount * o.derived_from.amount * 0.01
                                    else:
                                        amount = o.amount * (o.derived_from.amount * 0.01 * o.derived_from.derived_from.amount) * 0.01
                                self.env.cr.execute('execute insert_item_line(%s,%s,%s)', (item_id[0],o.name,-amount))
                                    
                            for e in nonstd_earnings:
                                self.env.cr.execute('execute insert_item_line(%s,%s,%s)', (item_id[0],e.name,e.amount))
                    
                    self.update({'state':'processed','total_net_payroll':total_net,'total_balance_payroll':total_net,'total_gross_payroll':total_gross,'total_tax_payroll':total_tax,'total_taxable_payroll':total_taxable, 'processing_time_payroll':(time.time() - tic)})
                    self.update({'payroll_summary_ids':dept_summary.values()})
                    self.env.cr.commit()
            
                    #Process subventions
                    subvention_list = []
                    for subv in subventions:
                        subvention_list.append({'department_id': subv.org_id.id,'name': subv.name,'active': subv.active,'amount': subv.amount,'payroll_id':self.id})
                    self.update({'subvention_item_ids':subvention_list})

                    #Send email to caller on completion
                    #message = ("Hello Sir,\nPayroll '" + self.name + "' has completed. Thank you.\n")
                    #vals = {'state': 'outgoing',
                    #        'subject': 'Payroll Processing Completed',
                    #        'body_html': '<pre>%s</pre>' % message,
                    #        'email_to': 'neeyeed@gmail.com',
                    #        'email_to': self.env.user.email,
                    #        'email_from': 'osun.payroll@gmail.com',
                    #}
                    #email_id = self.env['mail.mail'].create(vals, context=context)
                    #self.env['mail.mail'].send(email_id)
                    
                    if self.notify_emails:
                        sender = 'osun.payroll@gmail.com'
                        receivers = self.notify_emails
                        subject = 'Payroll Completed'
            
                        message = "Hello Sir,\nPayroll '" + self.name + "' has completed.\n\nThank you.\n"
                        smtp_obj = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
                        smtp_obj.ehlo()
                        #smtp_obj.starttls()
                        #smtp_obj.ehlo()
                        smtp_obj.login(user="osun.payroll@gmail.com", password="p@55w0rd1939")
                        new_message = '\r\n'.join([
                                        'To: %s' %receivers,
                                        'From: %s' % sender,
                                        'Subject: %s' %subject,
                                        '',
                                        message
                                        ])
                        smtp_obj.sendmail(sender, receivers, new_message)         
                        _logger.info("Email successfully sent to " + 'neeyeed@gmail.com')
                    
                if self.do_pension:                    
                    tic = time.time()
                    total_gross = 0
                    total_net = 0
                    
                    #List all pension deductions
                    deductions_pension = self.env['ng.state.payroll.deduction.pension'].search([('active', '=', True)])
                    _logger.info("Count deductions_pension= %d", len(deductions_pension))        
        
                    pensioners = self.env['hr.employee'].search([('active', '=', True), ('status_id.name', '=', 'PENSIONED')])
                    _logger.info("Count pensioners= %d", len(pensioners))        
                    
                    item_list = []
    
                    for pen in pensioners:
                        item_list_lines = []                
                        pension_amount = pen.annual_pension / 12
                        gross_amount = pension_amount
                        active_flag = False
                        if pen.status_id.name == 'PENSIONED':
                            active_flag = True
                        item_dict = {'employee_id':pen.id, 'active':active_flag, 'payroll_id':self.id, 'gross_income':pension_amount}
                        ded_amount = 0
                        item_list_lines.append({'name':'Monthly Pension', 'amount':pension_amount})
                        for ded in deductions_pension:
                            if len(ded.whitelist_ids) > 0 and pen in ded.whitelist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            if not pen in ded.blacklist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            pension_amount -= ded_amount
                            item_list_lines.append({'name':ded.name, 'amount':-ded_amount})
                        total_gross = total_gross + gross_amount
                        total_net = total_net + pension_amount                            
                        item_dict.update({'item_line_ids':item_list_lines, 'gross_income':gross_amount, 'net_income':pension_amount, 'balance_income':pension_amount})
                        item_list.append(item_dict)
                    
                    self.update({'pension_item_ids':item_list})                                    
                    self.update({'state':'processed','total_net_pension':total_net,'total_balance_pension':total_net,'total_gross_pension':total_gross, 'processing_time_pension':(time.time() - tic)})

                    #Send email to caller on completion
                    #message = ("Hello Sir,\nPayroll '" + self.name + "' has completed. Thank you.\n")
                    #vals = {'state': 'outgoing',
                    #        'subject': 'Payroll Processing Completed',
                    #        'body_html': '<pre>%s</pre>' % message,
                    #        'email_to': 'neeyeed@gmail.com',
                    #        #'email_to': self.env.user.email,
                    #        'email_from': 'neeyeed@gmail.com',
                    #}
                    #email_id = self.env['mail.mail'].create(vals, context=context)
                    #self.env['mail.mail'].send(email_id, auto_commit=True, context=context)
                    sender = 'osun.payroll@gmail.com'
                    receivers = 'neeyeed@gmail.com'
        
                    message = "Hello Sir,\nPayroll '" + self.name + "' has completed. Thank you.\n"
                    smtp_obj = smtplib.SMTP(host='smtp.gmail.com', port=587)
                    smtp_obj.ehlo()
                    smtp_obj.starttls()
                    smtp_obj.ehlo()
                    smtp_obj.login(user="osun.payroll@gmail.com", password="p@55w0rd1939")
                    smtp_obj.sendmail(sender, receivers, message)         
                    _logger.info("Email successfully sent to " + 'neeyeed@gmail.com')
                    
        return True    
                            
    @api.multi
    def finalize2(self, context=None):
        _logger.info("Calling finalize2...state = %s", self.state)
        
        #TODO Change ORM create and update calls to DB Cursor SQL calls
        
        if self.state == 'in_progress':
            if self.calendar_id:
                if self.do_payroll:
                    tic = time.time()
                    item_list = []
            
                    #List all tax rules
                    paye_taxrules = self.env['ng.state.payroll.taxrule'].search([('active', '=', 'True')])
                    
                    #Fetch all active employees *TODO* (and non-suspended employees)
                    employees = self.env['hr.employee'].search([('active', '=', 'True'), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
                    #employees = self.env['hr.employee'].search([('employee_no', 'in', ['65754','21978','37449','20925','11355','4599','22560','17771','4414','44552','30801','35323','32546','46842','31692','14867','58081','38892','10486','43932','40052','41927','32342','12507','7037','33280','41948','41944','17966','33498','32850','41969','79972','44957','16617','41520','36962','40917','47375','39139','41954','75063','32117','44436','41641','35637','44032','27535','78315','89000','73796','72297','88006','33686','31971','72773','72759','17781','17006','47208','65679','47929','87878','5107','5113','5084','05147_D','10868','12463','74083','84370','35370','6122','6123','6119','6148','1980','1936','1957','12460','33746','32017','75184','PP199','12026','12461','89040','86900','86904','86899','86897','86887','86889','86905','86902','86903','78632','34635','34700','34581','33514','34580','10616','4196','4153','4173','78404','73200','72110','72083','12090','40435','41637','3659','89014','5102','4146','4115','4144','4184','4075','4160','38250','44058','40933','10573','6449','5019','44071','43900','43905','43904','3654','3662','32454','33770','34609','31901','36897','34512','34479','31578','36384','34608','34489','30538','34835','38225','41797','88916','88893','86268','70972','44930','44055','PP196','PP197','PP198','78219','87195','87121','88751','88862','87056','88752','78298','87028','87196','87200','87217','88806','88396','78105','78167','88791','78265','86574','86591','88567','88662','88622','88568','78322','78324','78323','87036','87046','84001','88812','88813','78120','78119','78337','78209','88698','86461','86623','86621','86847','88378','78218','86525','86522','88366','86592','5099','5103','5078','74728','4182','41087','42024','72001','86028','36309','35622','86160','78217','87119','87183','87110','87142','88740','87067','88861','87097','88746','88738','87199','87118','87136','87108','87104','87211','87141','88674','88402','88403','88643','88520','88641','88486','88497','86520','86575','88481','86521','86506','88552','86515','88526','88387','88386','86236','87209','87206','78196','78184','87155','78197','78200','87022','78125','87124','88869','88796','87205','78124','87203','88736','87191','78310','78145','78144','88795','78134','88808','88850','78140','78135','78147','78148','78306','78253','78250','78252','78266','88734','88877','78171','87077','87081','78237','78228','88864','78172','78256','78247','87083','87087','87088','78244','87082','78233','88711','88684','86576','88710','86517','88547','88314','88658','88487','86518','88329','88652','86465','88599','86485','86486','88483','88610','88612','86484','88680','86494','86467','86512','86593','86012','78364','86251','86011','88917','88991','86242','86237','86267','88008','78389','88499','88642','88644','86587','86483','88544','88562','88659','88929','86273','86293','87030','78081','87149','87150','87147','78082','78121','78117','87134','78080','88857','87094','87044','87033','87055','87042','78112','78106','88866','78113','78111','88786','78341','87076','78343','88510','88664','88651','88450','88608','88470','88511','86510','86513','88513','86490','86504','88522','88976','86255','86247','88985','86294','86252','86222','86239','86269','88007','87176','86853','86852','78204','88872','88873','88797','87140','78215','78213','87175','87174','86250','86135','86285','86202','86171','86254','78386','86095','86162','86323','88712','88706','88654','88488','88576','88293','88705','88704','88655','88975','86168','86078','86169','86185','86024','86052','78414','86138','86136','86305','86300','87169','87168','86843','86842','86275','86627','86620','86141','86089','86292','86302','86638','86612','86622','86856','86860','86846','86316','86473','86629','86284','89051','89269','87171','87166','86240','86819','88673','89267','86848','88479','86260','86023','86201','88003','78246','86161','86244','78388','88896','88894','86155','78206','88731','78153','78377','88753','88019','88750','86079','86034','88913','86125','86087','88930','86199','88895','86499','78293','88732','86180','86597','86468','86523','88582','88860','86179','86139','86073','86235','86033','86154','86231','86232','88020','86322','86845','78395','86590','86464','88766','86571','86498','86812','86818','78270','86480','87072','87074','40043','67666','67670','72129','79905','67747','71814','72133','70975','66990','38218','38216','38219','42285','5100','5130','5068','5083','5098','5039','10598','10599','4150','40151','39322','89314','84071','84072','84564','84062','89860','89865','71444','71484','71486','88210','71482','71479','71446','71447','71445','71483','71485','71481','71480','71487','5049','75159','87557','78745','79954','70254','66996','66992','87564','67751','67669','71815','72141','71811','67654','72089','72021','68494_D','71998','75157','78757','44813','38959','39170','74692','74687','70580','70590','70591','74839','74701','68387','74696','78663','78664','75026','72086','45697','45688','65689','58514','41514','36320','30994','74675','44786','72816','41655','44639','58065','40542','38913','42538','27711','38455','25144','38560','41916','41363','7871','38660','121','6340','43641','42859','42936','6289','6299','6344'])])

                    _logger.info("Count employees= %d", len(employees))        
                    
                    total_gross = 0
                    total_net = 0
                    total_tax = 0
                    total_taxable = 0
                    
                    dept_summary = {}
            
                    for emp in employees:
                        #TODO When an employee has been reinstated in this calendar period,- 
                        #pick all previously inactive payroll items from previous calendar- 
                        #periods from the suspension month to current calendar period, move-
                        #them to current pay period and set them active
                        _logger2.info("---------------------------------------------")
                        _logger2.info("Name=%s", emp.name_related)
                        item_list_lines = []
                            
                        #Create Payroll Item and Payroll Item Lines
                        active_flag = False
                        if emp.status_id.name == 'ACTIVE':
                            active_flag = True
                        item_dict = {'employee_id':emp.id, 'active': active_flag, 'payroll_id': self.id}
                        item_line_gross = 0
                        item_line_leave = 0
                        item_line_deduction = 0
                        item_line_taxable = 0
                        item_line_relief = 200000
                        
                        #Calculate each standard earning
                        #for o in emp.standard_earnings.filtered(lambda r: r.active == True):
                        for o in emp.employee_earnings.filtered(lambda r: r.active == True):
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                amount = o.amount * o.derived_from.amount * 0.01
                            item_line_gross += amount
                            _logger2.info("Standard Earning[%s]=%f", o.name, amount)
                            item_list_lines.append({'name':o.name, 'amount':(amount / 12)})
                         
                        #Calculate each standard deduction
                        #for o in emp.standard_deductions.filtered(lambda r: r.active == True):
                        for o in emp.employee_deductions.filtered(lambda r: r.active == True):
                            amount = 0
                            if o.fixed:
                                amount = -o.amount
                            else:
                                if o.derived_from.fixed:
                                    amount = o.amount * o.derived_from.amount * 0.01
                                else:
                                    amount = o.amount * (o.derived_from.amount * 0.01 * o.derived_from.derived_from.amount) * 0.01
                            _logger2.info("Standard Deduction[%s]=%f", o.name, amount)
                            item_line_deduction += -amount
                            item_list_lines.append({'name':o.name, 'amount':(amount / 12)})

                        _logger2.info("Gross Income=%f", item_line_gross)
                        
                        percent_1percent = item_line_gross * 0.01
                        if percent_1percent > 200000:
                            item_line_relief = percent_1percent
                        item_line_relief += (item_line_gross * 0.2) #CRA relief
                        item_line_taxable = item_line_gross - item_line_relief
                        if item_line_taxable < 0:
                            item_line_taxable = 0
                        #Calculate PAYE Tax for each employee based on each taxable income items.
                        #TODO item_line_deduction should actually be reliefs - NHF, Pension, Party
                        total_taxable += (item_line_taxable / 12)
                        item_line_tax = 0
                        if item_line_taxable > 0:
                            prev_to_amount = 0
                            for taxrule in paye_taxrules:
                                if item_line_taxable - taxrule.to_amount >= 0:
                                    item_line_tax += ((taxrule.percentage / 100) * (taxrule.to_amount - prev_to_amount))
                                    _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (taxrule.to_amount - prev_to_amount), taxrule.percentage, item_line_tax)
                                    prev_to_amount = taxrule.to_amount
                                else:
                                    item_line_tax += ((taxrule.percentage / 100) * (item_line_taxable - prev_to_amount))
                                    _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (item_line_taxable - prev_to_amount), taxrule.percentage, item_line_tax)
                                    break
                           
                            #Apply 1% PAYE rule
                            tax_1percent = item_line_gross * 0.01
                            if item_line_tax < tax_1percent:
                                item_line_tax = tax_1percent                        
                        
                        item_line_net = item_line_gross - item_line_deduction - item_line_tax
                        
                        _logger2.info("Gross=%f", item_line_gross)
                        _logger2.info("Net=%f", item_line_net)
                        _logger2.info("Taxable=%f", item_line_taxable)
                        _logger2.info("PAYE=%f", item_line_tax)
                        
                        item_dict.update({'item_line_ids':item_list_lines})
                        if item_line_gross > 0:
                            total_gross = total_gross + (item_line_gross / 12)
                            total_net = total_net + (item_line_net / 12)
                            total_tax = total_tax + (item_line_tax / 12)
            
                            item_dict.update({'gross_income':(item_line_gross / 12),'net_income':(item_line_net / 12),'balance_income':(item_line_net / 12),'taxable_income':(item_line_taxable / 12),'paye_tax':(item_line_tax / 12),'leave_allowance':item_line_leave,'active':emp.active})
            
                            if not dept_summary.has_key(emp.department_id.id):
                                dept_summary[emp.department_id.id] = {'department_id':emp.department_id.id,'payroll_id':self.id,'total_taxable_income':0,'total_gross_income':0,'total_net_income':0,'total_paye_tax':0,'total_leave_allowance':0}
                            else:
                                dept_summary[emp.department_id.id]['total_taxable_income'] += (item_line_taxable / 12)
                                dept_summary[emp.department_id.id]['total_gross_income'] += (item_line_gross / 12)
                                dept_summary[emp.department_id.id]['total_net_income'] += (item_line_net / 12)
                                dept_summary[emp.department_id.id]['total_paye_tax'] += (item_line_tax / 12)
                                dept_summary[emp.department_id.id]['total_leave_allowance'] += item_line_leave
                        else:
                            item_dict.update({'gross_income':(item_line_gross / 12),'net_income':(item_line_net / 12),'balance_income':(item_line_net / 12),'taxable_income':(item_line_taxable / 12),'paye_tax':(item_line_tax / 12),'leave_allowance':item_line_leave,'active':emp.active,'resolve':True})
                            
                        item_list.append(item_dict)
                    
                    self.update({'payroll_item_ids':item_list})
                    self.update({'state':'processed','total_net_payroll':total_net,'total_balance_payroll':total_net,'total_gross_payroll':total_gross,'total_tax_payroll':total_tax,'total_taxable_payroll':total_taxable, 'processing_time_payroll':(time.time() - tic)})
                    self.update({'payroll_summary_ids':dept_summary.values()})
                    
                if self.do_pension:                    
                    tic = time.time()
                    total_gross = 0
                    total_net = 0
                    
                    #List all pension deductions
                    deductions_pension = self.env['ng.state.payroll.deduction.pension'].search([('active', '=', 'True')])
                    _logger.info("Count deductions_pension= %d", len(deductions_pension))        
        
                    pensioners = self.env['hr.employee'].search([('active', '=', 'True'), ('status_id.name', '=', 'PENSIONED')])
                    _logger.info("Count pensioners= %d", len(pensioners))        
                    
                    item_list = []
    
                    for pen in pensioners:
                        item_list_lines = []                
                        pension_amount = pen.annual_pension / 12
                        gross_amount = pension_amount
                        active_flag = False
                        if pen.status_id.name == 'PENSIONED':
                            active_flag = True
                        item_dict = {'employee_id':pen.id, 'active':active_flag, 'payroll_id':self.id, 'gross_income':pension_amount}
                        ded_amount = 0
                        item_list_lines.append({'name':'Monthly Pension', 'amount':pension_amount})
                        for ded in deductions_pension:
                            if len(ded.whitelist_ids) > 0 and pen in ded.whitelist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            if not pen in ded.blacklist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            pension_amount -= ded_amount
                            item_list_lines.append({'name':ded.name, 'amount':-ded_amount})
                        total_gross = total_gross + gross_amount
                        total_net = total_net + pension_amount                            
                        item_dict.update({'item_line_ids':item_list_lines, 'gross_income':gross_amount, 'net_income':pension_amount, 'balance_income':pension_amount})
                        item_list.append(item_dict)
                    
                    self.update({'pension_item_ids':item_list})                                    
                    self.update({'state':'processed','total_net_pension':total_net,'total_balance_pension':total_net,'total_gross_pension':total_gross, 'processing_time_pension':(time.time() - tic)})

                    #Send email to caller on completion
                    message = ("Hello Sir,\nPayroll '" + self.name + "' has completed. Thank you.\n")
                    vals = {'state': 'outgoing',
                            'subject': 'Payroll Processing Completed',
                            'body_html': '<pre>%s</pre>' % message,
                            'email_to': 'neeyeed@gmail.com',
                            #'email_to': self.env.user.email,
                            'email_from': 'neeyeed@gmail.com',
                    }
                    email_id = self.env['mail.mail'].create(vals, context=context)
                    self.env['mail.mail'].send(email_id)
        return True                    
            
    def dry_run(self):
        _logger.info("Calling finalize...state = %s", self.state)
        if self.in_progress:
            raise osv.except_osv(_('Info'), _('Processing already in progress.'))
                    
        prev_state = self.state
        if not self.state == 'in_progress':        
            if self.calendar_id and self.state == 'draft':
                self.set_in_progress()
                
                if self.do_payroll:
                    tic = time.time()
                    item_list = []
                            
                    #List all subvention earnings for this calendar period
                    subventions = self.env['ng.state.payroll.subvention'].search([('active', '=', 'True'), ('calendar_id', '=', self.calendar_id.id)])
            
                    #List all tax rules
                    paye_taxrules = self.env['ng.state.payroll.taxrule'].search([('active', '=', 'True')])
                    
                    #List all standard earnings for this calendar period
                    earnings_nonstd_all = self.env['ng.state.payroll.earning.nonstd'].search([('active', '=', 'True'), ('calendars.id', '=', self.calendar_id.id)], order='employee_id')
                    _logger.info("Count earnings_nonstd= %d", len(earnings_nonstd_all))        
                    
                    #List all non-standard deductions for this calendar period
                    deductions_nonstd_all = self.env['ng.state.payroll.deduction.nonstd'].search([('active', '=', 'True'), ('calendars.id', '=', self.calendar_id.id)], order='employee_id')
                    _logger.info("Count deductions_nonstd= %d", len(deductions_nonstd_all))        
                    
                    #Fetch all active employees *TODO* (and non-suspended employees)
                    employees = self.env['hr.employee'].search([('active', '=', 'True'), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
                    _logger.info("Count employees= %d", len(employees))        
                    
                    total_gross = 0
                    total_net = 0
                    total_tax = 0
                    total_taxable = 0
                    
                    dept_summary = {}
            
                    for emp in employees:
                        #TODO When an employee has been reinstated in this calendar period,- 
                        #pick all previously inactive payroll items from previous calendar- 
                        #periods from the suspension month to current calendar period, move-
                        #them to current pay period and set them active
                        item_list_lines = []
                
                        earnings_standard = self.env['ng.state.payroll.earning.standard'].search([('active', '=', 'True'), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])
                        deductions_standard = self.env['ng.state.payroll.deduction.standard'].search([('active', '=', 'True'), ('payscheme_id', '=', emp.payscheme_id.id), ('level_id', '=', emp.level_id.id)])
                            
                        #Create Payroll Item and Payroll Item Lines
                        active_flag = False
                        if emp.status_id.name == 'ACTIVE':
                            active_flag = True
                        item_dict = {'employee_id':emp.id, 'active': active_flag, 'payroll_id': self.id}
                        item_line_income = 0
                        item_line_gross = 0
                        item_line_leave = 0
                        item_line_deduction = 0
                        item_line_relief = 0
                        item_line_earnings_standard = 0
                        item_line_earnings_nonstd = 0
                        item_line_deductions_standard = 0
                        item_line_deductions_nonstd = 0
                        
                        basic_salary = False
                        #Calculate each standard earning
                        for o in earnings_standard:
                            if o.name == 'BASIC SALARY':
                                basic_salary = o
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                amount = o.amount * o.derived_from.amount * 0.01
                            #_logger2.info("Standard Earning[%s]=%f", o.name, amount)
                            item_list_lines.append({'name':o.name, 'amount':amount})
                            item_line_gross += amount
                            item_line_earnings_standard += amount
                            #if o.taxable:
                                #item_line_taxable += amount
                         
                        #Calculate each standard deduction
                        for o in deductions_standard:
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                if o.derived_from.fixed:
                                    amount = o.amount * o.derived_from.amount * 0.01
                                else:
                                    amount = o.amount * (o.derived_from.amount * 0.01 * o.derived_from.derived_from.amount) * 0.01
                            #_logger2.info("Standard Deduction[%s]=%f", o.name, -amount)
                            item_list_lines.append({'name':o.name, 'amount':-amount})
                            item_line_deduction += amount
                            item_line_deductions_standard += amount
                            if o.name.startswith('PENSION FROM') or o.name == 'NHF' or o.name == 'PARTY DEDUCTION':
                                item_line_relief += amount
                                #_logger2.info("Relief[%s]=%f", o.name, amount)
                                  
                            #item_line_taxable -= amount 
                                
                        earnings_nonstd = earnings_nonstd_all.filtered(lambda r: r.employee_id.id == emp.id)
                        earnings_nonstd_all = earnings_nonstd_all - earnings_nonstd
                        #Calculate each non-standard earning
                        for e in earnings_nonstd:
                            item_line_gross += (e.amount)
                            item_line_earnings_nonstd += (e.amount)
                            #if earnings_nonstd[idx_nonstd_earnings].taxable:
                                #item_line_taxable += earnings_nonstd[idx_nonstd_earnings].amount
                            #_logger2.info("Nonstandard Earning[%s]=%f", e.name, (e.amount))
                            item_list_lines.append({'name':e.name, 'amount':(e.amount)})
                
                        deductions_nonstd = deductions_nonstd_all.filtered(lambda r: r.employee_id.id == emp.id)
                        deductions_nonstd_all = deductions_nonstd_all - deductions_nonstd
                        #Calculate each non-standard deduction
                        for d in deductions_nonstd:
                            #_logger2.info("Nonstandard Deduction[%s]=%f", d.name, (d.amount))
                            #item_line_taxable -= deductions_nonstd[idx_nonstd_deductions].amount
                            #TODO Create a configuration entity to manage reliefs
                            item_line_deduction += (d.amount)
                            item_line_deductions_nonstd += (d.amount)
                            if d.name.startswith('PENSION FROM') or d.name == 'NHF' or d.name == 'PARTY DEDUCTION':
                                item_line_relief += (d.amount)
                                #_logger2.info("Relief[%s]=%f", d.name, (d.amount))
                                
                        #Pay Leave Allowance for employees on birthdays that fall in this pay calendar
                        #Add Leave allowance to taxable and gross income
                        item_line_leave = 0
                        leave_allowance = self.env['ng.state.payroll.leaveallowance'].search([('payscheme_id', '=', emp.payscheme_id.id)])
                        if leave_allowance and basic_salary:
                            item_line_leave = basic_salary.amount * leave_allowance.percentage / 100
                            item_line_income += (item_line_leave + item_line_gross)
                            #_logger2.info("Leave Allowance=%f", item_line_leave)
        
                        #_logger2.info("Annual Income=%f", item_line_income)
                                
                        #Pro-rate for retiring employees
                        item_line_retiring = False
                        #_logger2.info("Retirement Date=%s", emp.retirement_due_date)
                        if emp.retirement_due_date:
                            retirement_month = datetime.strptime(emp.retirement_due_date, '%Y-%m-%d').strftime('%m')
                            retirement_year = datetime.strptime(emp.retirement_due_date, '%Y-%m-%d').strftime('%Y')
                            pay_month = datetime.strptime(self.calendar_id.from_date, '%Y-%m-%d').strftime('%m')
                            pay_year = datetime.strptime(self.calendar_id.from_date, '%Y-%m-%d').strftime('%Y')
                            if retirement_month == pay_month and retirement_year == pay_year:
                                item_line_retiring = True
                                retirement_day = datetime.strptime(emp.retirement_due_date, '%Y-%m-%d').strftime('%d')
                                item_line_gross *= (float(retirement_day) / 30.0)
                                #_logger2.info("Pro-rated Gross=%f", item_line_gross)
                                #item_line_taxable *= (float(retirement_day) / 30)
                            
                        #Calculate PAYE Tax for each employee based on each taxable income items.
                        #TODO item_line_deduction should actually be reliefs - NHF, Pension, Party
                        item_line_relief += (item_line_income * 0.2 + 200000) #CRA relief
                        item_line_taxable = item_line_income - item_line_relief
                        total_taxable += (item_line_taxable / 12)
                        item_line_tax = 0
                        prev_to_amount = 0
                        for taxrule in paye_taxrules:
                            if item_line_taxable - taxrule.to_amount >= 0:
                                item_line_tax += ((taxrule.percentage / 100) * (taxrule.to_amount - prev_to_amount))
                                #_logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (taxrule.to_amount - prev_to_amount), taxrule.percentage, item_line_tax)
                                prev_to_amount = taxrule.to_amount
                            else:
                                item_line_tax += ((taxrule.percentage / 100) * (item_line_taxable - prev_to_amount))
                                #_logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (item_line_taxable - prev_to_amount), taxrule.percentage, item_line_tax)
                                break
                        
                        #Apply 1% PAYE rule
                        tax_1percent = item_line_income * 0.01
                        if item_line_tax < tax_1percent:
                            item_line_tax = tax_1percent 
                        
                        item_line_net = item_line_gross - item_line_deduction - item_line_tax
                        
                        monthly_gross = item_line_earnings_nonstd + item_line_earnings_standard / 12
                        monthly_deductions = item_line_deductions_nonstd + item_line_deductions_standard / 12
                        monthly_net = monthly_gross - monthly_deductions - item_line_tax / 12
                        
                        #_logger2.info("Gross=%f", item_line_gross)
                        #_logger2.info("Net=%f", item_line_net)
                        #_logger2.info("Relief=%f", item_line_relief)
                        #_logger2.info("Taxable=%f", item_line_taxable)
                        #_logger2.info("PAYE=%f", item_line_tax)
                        
                        #TODO Item list details are lost when persisted.
                        item_dict.update({'item_line_ids':item_list_lines})
                        if monthly_net > 0:
                            total_gross = total_gross + monthly_gross
                            total_net = total_net + monthly_net
                            if item_line_tax > 0:
                                total_tax = total_tax + (item_line_tax / 12)
            
                            item_dict.update({'gross_income':monthly_gross,'net_income':monthly_net,'balance_income':monthly_net,'taxable_income':(item_line_taxable / 12),'paye_tax':(item_line_tax / 12),'leave_allowance':item_line_leave,'active':emp.active,'retiring':item_line_retiring})
            
                            if not dept_summary.has_key(emp.department_id.id):
                                dept_summary[emp.department_id.id] = {'department_id':emp.department_id.id,'payroll_id':self.id,'total_taxable_income':0,'total_gross_income':0,'total_net_income':0,'total_paye_tax':0,'total_leave_allowance':0}
                            else:
                                dept_summary[emp.department_id.id]['total_taxable_income'] += (item_line_taxable / 12)
                                dept_summary[emp.department_id.id]['total_gross_income'] += (item_line_gross / 12)
                                dept_summary[emp.department_id.id]['total_net_income'] += (item_line_net / 12)
                                dept_summary[emp.department_id.id]['total_paye_tax'] += (item_line_tax / 12)
                                dept_summary[emp.department_id.id]['total_leave_allowance'] += item_line_leave
                        else:
                            item_dict.update({'gross_income':0,'net_income':0,'balance_income':0,'taxable_income':0,'paye_tax':0,'leave_allowance':0,'active':emp.active,'retiring':item_line_retiring,'resolve':True})
                            
                        item_list.append(item_dict)
                    
                    self.payroll_item_ids = item_list
                    self.total_net_payroll = total_net
                    self.total_balance_payroll = total_net
                    self.total_gross_payroll = total_gross
                    self.total_taxable_payroll = total_taxable
                    self.total_tax_payroll = total_tax
                    self.processing_time = (time.time() - tic)
                    self.payroll_summary_ids = dept_summary.values()
            
                    #Process subventions
                    subvention_list = []
                    for subv in subventions:
                        subvention_list.append({'department_id': subv.org_id.id,'name': subv.name,'active': subv.active,'amount': subv.amount,'payroll_id':self.id})
                    self.subvention_item_ids = subvention_list
                    
                if self.do_pension:                    
                    tic = time.time()
                    total_gross = 0
                    total_net = 0
                    
                    #List all pension deductions
                    deductions_pension = self.env['ng.state.payroll.deduction.pension'].search([('active', '=', 'True')])
                    _logger.info("Count deductions_pension= %d", len(deductions_pension))        
        
                    pensioners = self.env['hr.employee'].search([('active', '=', 'True'), ('status_id.name', '=', 'PENSIONED')])
                    _logger.info("Count pensioners= %d", len(pensioners))        
                    
                    item_list = []
    
                    for pen in pensioners:
                        item_list_lines = []                
                        pension_amount = pen.annual_pension / 12
                        gross_amount = pension_amount
                        active_flag = False
                        if pen.status_id.name == 'PENSIONED':
                            active_flag = True
                        item_dict = {'employee_id':pen.id, 'active':active_flag, 'payroll_id':self.id, 'gross_income':pension_amount}
                        ded_amount = 0
                        item_list_lines.append({'name':'Monthly Pension', 'amount':pension_amount})
                        for ded in deductions_pension:
                            if len(ded.whitelist_ids) > 0 and pen in ded.whitelist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            if not pen in ded.blacklist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            pension_amount -= ded_amount
                            item_list_lines.append({'name':ded.name, 'amount':-ded_amount})
                        total_gross = total_gross + gross_amount
                        total_net = total_net + pension_amount                            
                        #TODO Item list details are lost when persisted.
                        item_dict.update({'item_line_ids':item_list_lines, 'gross_income':gross_amount, 'net_income':pension_amount, 'balance_income':pension_amount})
                        item_list.append(item_dict)
                    
                    self.pension_item_ids = item_list                                    
                    self.total_net_pension = total_net
                    self.total_balance_pension = total_net
                    self.total_gross_pension = total_gross
                    self.processing_time = (time.time() - tic)
                
        if (self.do_payroll or self.do_pension) and self.state == 'in_progress':
            self.update({'state':prev_state})
            
    @api.onchange('do_dry_run')
    def dry_run2(self):
        _logger.info("Calling dry_run2...state = %s", self.state)
        if self.in_progress:
            raise osv.except_osv(_('Info'), _('Processing already in progress.'))
                    
        if not self.state == 'in_progress':        
            if self.calendar_id and self.state == 'draft':
                if self.do_payroll:
                    tic = time.time()
                    item_list = []
                            
                    #List all tax rules
                    paye_taxrules = self.env['ng.state.payroll.taxrule'].search([('active', '=', 'True')])
                    
                    #Fetch all active employees *TODO* (and non-suspended employees)
                    employees = self.env['hr.employee'].search([('active', '=', 'True'), '|', ('status_id.name', '=', 'ACTIVE'), ('status_id.name', '=', 'SUSPENDED')], order='id')
                    #employees = self.env['hr.employee'].search([('employee_no', 'in', ['65754','21978','37449','20925','11355','4599','22560','17771','4414','44552','30801','35323','32546','46842','31692','14867','58081','38892','10486','43932','40052','41927','32342','12507','7037','33280','41948','41944','17966','33498','32850','41969','79972','44957','16617','41520','36962','40917','47375','39139','41954','75063','32117','44436','41641','35637','44032','27535','78315','89000','73796','72297','88006','33686','31971','72773','72759','17781','17006','47208','65679','47929','87878','5107','5113','5084','05147_D','10868','12463','74083','84370','35370','6122','6123','6119','6148','1980','1936','1957','12460','33746','32017','75184','PP199','12026','12461','89040','86900','86904','86899','86897','86887','86889','86905','86902','86903','78632','34635','34700','34581','33514','34580','10616','4196','4153','4173','78404','73200','72110','72083','12090','40435','41637','3659','89014','5102','4146','4115','4144','4184','4075','4160','38250','44058','40933','10573','6449','5019','44071','43900','43905','43904','3654','3662','32454','33770','34609','31901','36897','34512','34479','31578','36384','34608','34489','30538','34835','38225','41797','88916','88893','86268','70972','44930','44055','PP196','PP197','PP198','78219','87195','87121','88751','88862','87056','88752','78298','87028','87196','87200','87217','88806','88396','78105','78167','88791','78265','86574','86591','88567','88662','88622','88568','78322','78324','78323','87036','87046','84001','88812','88813','78120','78119','78337','78209','88698','86461','86623','86621','86847','88378','78218','86525','86522','88366','86592','5099','5103','5078','74728','4182','41087','42024','72001','86028','36309','35622','86160','78217','87119','87183','87110','87142','88740','87067','88861','87097','88746','88738','87199','87118','87136','87108','87104','87211','87141','88674','88402','88403','88643','88520','88641','88486','88497','86520','86575','88481','86521','86506','88552','86515','88526','88387','88386','86236','87209','87206','78196','78184','87155','78197','78200','87022','78125','87124','88869','88796','87205','78124','87203','88736','87191','78310','78145','78144','88795','78134','88808','88850','78140','78135','78147','78148','78306','78253','78250','78252','78266','88734','88877','78171','87077','87081','78237','78228','88864','78172','78256','78247','87083','87087','87088','78244','87082','78233','88711','88684','86576','88710','86517','88547','88314','88658','88487','86518','88329','88652','86465','88599','86485','86486','88483','88610','88612','86484','88680','86494','86467','86512','86593','86012','78364','86251','86011','88917','88991','86242','86237','86267','88008','78389','88499','88642','88644','86587','86483','88544','88562','88659','88929','86273','86293','87030','78081','87149','87150','87147','78082','78121','78117','87134','78080','88857','87094','87044','87033','87055','87042','78112','78106','88866','78113','78111','88786','78341','87076','78343','88510','88664','88651','88450','88608','88470','88511','86510','86513','88513','86490','86504','88522','88976','86255','86247','88985','86294','86252','86222','86239','86269','88007','87176','86853','86852','78204','88872','88873','88797','87140','78215','78213','87175','87174','86250','86135','86285','86202','86171','86254','78386','86095','86162','86323','88712','88706','88654','88488','88576','88293','88705','88704','88655','88975','86168','86078','86169','86185','86024','86052','78414','86138','86136','86305','86300','87169','87168','86843','86842','86275','86627','86620','86141','86089','86292','86302','86638','86612','86622','86856','86860','86846','86316','86473','86629','86284','89051','89269','87171','87166','86240','86819','88673','89267','86848','88479','86260','86023','86201','88003','78246','86161','86244','78388','88896','88894','86155','78206','88731','78153','78377','88753','88019','88750','86079','86034','88913','86125','86087','88930','86199','88895','86499','78293','88732','86180','86597','86468','86523','88582','88860','86179','86139','86073','86235','86033','86154','86231','86232','88020','86322','86845','78395','86590','86464','88766','86571','86498','86812','86818','78270','86480','87072','87074','40043','67666','67670','72129','79905','67747','71814','72133','70975','66990','38218','38216','38219','42285','5100','5130','5068','5083','5098','5039','10598','10599','4150','40151','39322','89314','84071','84072','84564','84062','89860','89865','71444','71484','71486','88210','71482','71479','71446','71447','71445','71483','71485','71481','71480','71487','5049','75159','87557','78745','79954','70254','66996','66992','87564','67751','67669','71815','72141','71811','67654','72089','72021','68494_D','71998','75157','78757','44813','38959','39170','74692','74687','70580','70590','70591','74839','74701','68387','74696','78663','78664','75026','72086','45697','45688','65689','58514','41514','36320','30994','74675','44786','72816','41655','44639','58065','40542','38913','42538','27711','38455','25144','38560','41916','41363','7871','38660','121','6340','43641','42859','42936','6289','6299','6344'])])

                    _logger.info("Count employees= %d", len(employees))        
                    
                    total_gross = 0
                    total_net = 0
                    total_tax = 0
                    total_taxable = 0
                    
                    dept_summary = {}
            
                    for emp in employees:
                        #TODO When an employee has been reinstated in this calendar period,- 
                        #pick all previously inactive payroll items from previous calendar- 
                        #periods from the suspension month to current calendar period, move-
                        #them to current pay period and set them active
                        _logger2.info("---------------------------------------------")
                        _logger2.info("Name=%s", emp.name_related)
                        item_list_lines = []
                            
                        #Create Payroll Item and Payroll Item Lines
                        active_flag = False
                        if emp.status_id.name == 'ACTIVE':
                            active_flag = True
                        item_dict = {'employee_id':emp.id, 'active': active_flag, 'payroll_id': self.id}
                        item_line_gross = 0
                        item_line_leave = 0
                        item_line_deduction = 0
                        item_line_taxable = 0
                        item_line_relief = 200000
                        
                        #Calculate each standard earning
                        #for o in emp.standard_earnings.filtered(lambda r: r.active == True):
                        for o in emp.employee_earnings.filtered(lambda r: r.active == True):
                            amount = 0
                            if o.fixed:
                                amount = o.amount
                            else:
                                amount = o.amount * o.derived_from.amount * 0.01
                            item_line_gross += amount
                            _logger2.info("Standard Earning[%s]=%f", o.name, amount)
                            item_list_lines.append({'name':o.name, 'amount':(amount / 12)})
                         
                        #Calculate each standard deduction
                        #for o in emp.standard_deductions.filtered(lambda r: r.active == True):
                        for o in emp.employee_deductions.filtered(lambda r: r.active == True):
                            amount = 0
                            if o.fixed:
                                amount = -o.amount
                            else:
                                if o.derived_from.fixed:
                                    amount = o.amount * o.derived_from.amount * 0.01
                                else:
                                    amount = o.amount * (o.derived_from.amount * 0.01 * o.derived_from.derived_from.amount) * 0.01
                            _logger2.info("Standard Deduction[%s]=%f", o.name, amount)
                            item_line_deduction += -amount
                            item_list_lines.append({'name':o.name, 'amount':(amount / 12)})

                        _logger2.info("Gross Income=%f", item_line_gross)
                        
                        percent_1percent = item_line_gross * 0.01
                        if percent_1percent > 200000:
                            item_line_relief = percent_1percent
                        item_line_relief += (item_line_gross * 0.2) #CRA relief
                        item_line_taxable = item_line_gross - item_line_deduction - item_line_relief
                        #Calculate PAYE Tax for each employee based on each taxable income items.
                        #TODO item_line_deduction should actually be reliefs - NHF, Pension, Party
                        total_taxable += (item_line_taxable / 12)
                        item_line_tax = 0
                        prev_to_amount = 0
                        for taxrule in paye_taxrules:
                            if item_line_taxable - taxrule.to_amount >= 0:
                                item_line_tax += ((taxrule.percentage / 100) * (taxrule.to_amount - prev_to_amount))
                                _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (taxrule.to_amount - prev_to_amount), taxrule.percentage, item_line_tax)
                                prev_to_amount = taxrule.to_amount
                            else:
                                item_line_tax += ((taxrule.percentage / 100) * (item_line_taxable - prev_to_amount))
                                _logger2.info("Amount=%f,Percentage=%f, PAYE=%f", (item_line_taxable - prev_to_amount), taxrule.percentage, item_line_tax)
                                break
                       
                        #Apply 1% PAYE rule
                        tax_1percent = item_line_taxable * 0.01
                        if item_line_tax < tax_1percent:
                            item_line_tax = tax_1percent                        
                        
                        item_line_net = item_line_gross - item_line_deduction - item_line_tax
                        
                        _logger2.info("Gross=%f", item_line_gross)
                        _logger2.info("Net=%f", item_line_net)
                        _logger2.info("Taxable=%f", item_line_taxable)
                        _logger2.info("PAYE=%f", item_line_tax)
                        
                        #TODO Item list details are lost when persisted.
                        item_dict.update({'item_line_ids':item_list_lines})
                        if item_line_gross > 0:
                            total_gross = total_gross + (item_line_gross / 12)
                            total_net = total_net + (item_line_net / 12)
                            total_tax = total_tax + (item_line_tax / 12)
            
                            item_dict.update({'gross_income':(item_line_gross / 12),'net_income':(item_line_net / 12),'balance_income':(item_line_net / 12),'taxable_income':(item_line_taxable / 12),'paye_tax':(item_line_tax / 12),'leave_allowance':item_line_leave,'active':emp.active})
            
                            if not dept_summary.has_key(emp.department_id.id):
                                dept_summary[emp.department_id.id] = {'department_id':emp.department_id.id,'payroll_id':self.id,'total_taxable_income':0,'total_gross_income':0,'total_net_income':0,'total_paye_tax':0,'total_leave_allowance':0}
                            else:
                                dept_summary[emp.department_id.id]['total_taxable_income'] += (item_line_taxable / 12)
                                dept_summary[emp.department_id.id]['total_gross_income'] += (item_line_gross / 12)
                                dept_summary[emp.department_id.id]['total_net_income'] += (item_line_net / 12)
                                dept_summary[emp.department_id.id]['total_paye_tax'] += (item_line_tax / 12)
                                dept_summary[emp.department_id.id]['total_leave_allowance'] += item_line_leave
                        else:
                            item_dict.update({'gross_income':(item_line_gross / 12),'net_income':(item_line_net / 12),'balance_income':(item_line_net / 12),'taxable_income':(item_line_taxable / 12),'paye_tax':(item_line_tax / 12),'leave_allowance':item_line_leave,'active':emp.active,'resolve':True})
                            
                        item_list.append(item_dict)
                    
                    self.payroll_item_ids = item_list
                    self.total_net_payroll = total_net
                    self.total_balance_payroll = total_net
                    self.total_gross_payroll = total_gross
                    self.total_taxable_payroll = total_taxable
                    self.total_tax_payroll = total_tax
                    self.processing_time_payroll = (time.time() - tic)
                    self.payroll_summary_ids = dept_summary.values()
                    self.state = 'processed'
                    
                if self.do_pension:                    
                    tic = time.time()
                    total_gross = 0
                    total_net = 0
                    
                    #List all pension deductions
                    deductions_pension = self.env['ng.state.payroll.deduction.pension'].search([('active', '=', 'True')])
                    _logger.info("Count deductions_pension= %d", len(deductions_pension))        
        
                    pensioners = self.env['hr.employee'].search([('active', '=', 'True'), ('status_id.name', '=', 'PENSIONED')])
                    _logger.info("Count pensioners= %d", len(pensioners))        
                    
                    item_list = []
    
                    for pen in pensioners:
                        item_list_lines = []                
                        pension_amount = pen.annual_pension / 12
                        gross_amount = pension_amount
                        active_flag = False
                        if pen.status_id.name == 'PENSIONED':
                            active_flag = True
                        item_dict = {'employee_id':pen.id, 'active':active_flag, 'payroll_id':self.id, 'gross_income':pension_amount}
                        ded_amount = 0
                        item_list_lines.append({'name':'Monthly Pension', 'amount':pension_amount})
                        for ded in deductions_pension:
                            if len(ded.whitelist_ids) > 0 and pen in ded.whitelist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            if not pen in ded.blacklist_ids:
                                if not ded.fixed:
                                    ded_amount = pension_amount * ded.amount / 100
                                else:
                                    ded_amount = ded.amount
                            pension_amount -= ded_amount
                            item_list_lines.append({'name':ded.name, 'amount':-ded_amount})
                        total_gross = total_gross + gross_amount
                        total_net = total_net + pension_amount                            
                        #TODO Item list details are lost when persisted.
                        item_dict.update({'item_line_ids':item_list_lines, 'gross_income':gross_amount, 'net_income':pension_amount, 'balance_income':pension_amount})
                        item_list.append(item_dict)
                    
                    self.pension_item_ids = item_list                                    
                    self.total_net_pension = total_net
                    self.total_balance_pension = total_net
                    self.total_gross_pension = total_gross
                    self.processing_time_pension = (time.time() - tic)
                    self.state = 'processed'
                                        
class ng_state_payroll_promotion(models.Model):
    '''
    Employee Promotion
    '''
    _name = "ng.state.payroll.promotion"
    _description = 'Employee Promotion'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'promotion_rule_id': fields.many2one('ng.state.payroll.promotion.rule', 'Promotion Rule'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True),
        'promotion_type': fields.selection([
            ('auto', 'Automatic'),
            ('manual', 'Manual'),
        ], 'Type', readonly=True),
        'date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'end_date': fields.date('End Date', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'acting': fields.boolean('Acting Capacity', help='Tick check-box if the employee is promoted in acting capacity'),
        'from_pay_category_id': fields.many2one('ng.state.payroll.paycategory', 'From Step'),
        'from_pay_scheme_id': fields.many2one('ng.state.payroll.payscheme', 'From Pay Scheme'),
        'from_grade_level': fields.selection([
            (1, 'GL-1'),
            (2, 'GL-2'),
            (3, 'GL-3'),
            (4, 'GL-4'),
            (5, 'GL-5'),
            (6, 'GL-6'),
            (7, 'GL-7'),
            (8, 'GL-8'),
            (9, 'GL-9'),
            (10, 'GL-10'),
            (12, 'GL-12'),
            (13, 'GL-13'),
            (14, 'GL-14'),
            (15, 'GL-15'),
            (16, 'GL-16'),
            (17, 'GL-17'),
        ], 'From Grade Level'),
        'to_pay_category_id': fields.many2one('ng.state.payroll.paycategory', 'To Step'),
        'to_pay_scheme_id': fields.many2one('ng.state.payroll.payscheme', 'To Pay Scheme'),
        'to_grade_level': fields.selection([
            (1, 'GL-1'),
            (2, 'GL-2'),
            (3, 'GL-3'),
            (4, 'GL-4'),
            (5, 'GL-5'),
            (6, 'GL-6'),
            (7, 'GL-7'),
            (8, 'GL-8'),
            (9, 'GL-9'),
            (10, 'GL-10'),
            (12, 'GL-12'),
            (13, 'GL-13'),
            (14, 'GL-14'),
            (15, 'GL-15'),
            (16, 'GL-16'),
            (17, 'GL-17'),
        ], 'To Grade Level'),
    }

    _rec_name = 'date'

    _defaults = {
        'state': 'draft',
        'promotion_type': 'manual'
    }

    _track = {
        'state': {
            'ng_state_payroll_promotion.mt_alert_promo_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'ng_state_payroll_promotion.mt_alert_promo_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_promotion.mt_alert_promo_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _needaction_domain_get(self, cr, uid, context=None):
        users_obj = self.pool.get('res.users')

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete Promotion!'),
                    _('Promotion has been initiated. Either cancel the promotion or create another promotion to undo it.')
                )

        return super(ng_state_payroll_promotion, self).unlink(cr, uid, ids, context=context)

    def effective_date_in_future(self, cr, uid, ids, context=None):
        today = datetime.now().date()
        for xfer in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                xfer.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
        employee_obj = self.pool.get('hr.employee')
        data = employee_obj.read(
            cr, uid, employee_id, ['state', 'retirement_due_date'], context=context) 
        if data.get('retirement_due_date', False) and data['retirement_due_date'] != '':
            retirementDate = datetime.strptime(
                data['retirement_due_date'], DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(
                effective_date, DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= retirementDate:
                raise orm.except_orm(
                    _('Warning!'),
                    _('The retirement date is on or before the effective '
                      'date of the transfer.')
                )
                
        return True

    def promotion_state_confirm(self, cr, uid, ids, context=None):
        for promo in self.browse(cr, uid, ids, context=context):
            _logger.info("before state_confirm - %d", uid)
            self._check_state(
                cr, uid, promo.employee_id.id, promo.date, context=context)
            self.write(cr, uid, promo.id, {'state': 'confirm'}, context=context)
            _logger.info("after state_confirm - %d", uid)

        return True

    def promotion_state_done(self, cr, uid, ids, context=None):
        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for promo in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                promo.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, promo.employee_id.id, promo.date,
                    context=context)
                #TODO Add earnings and deductions to dictionary
                employee_obj.write(
                    cr, uid, promo.employee_id.id, {
                        'resolved_earn_dedt': False,
                        'last_promotion_date': promo.date,
                        'paycategory_id': promo.to_pay_category_id.id,
                        'payscheme_id': promo.to_pay_category_id.id,
                        'grade_level': promo.grade_level},
                    context=context)
                self.write(
                    cr, uid, promo.id, {'state': 'done'}, context=context)
            else:
                return False

        return True

    def try_pending_promotions(self, cr, uid, context=None):
        """Completes pending promotions. Called from
        the scheduler."""

        promo_obj = self.pool.get('ng.state.payroll.promotion')
        today = datetime.now().date()
        promo_ids = promo_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'ng.state.payroll.promotion', promo.id, 'signal_done', cr)
         for promo in self.browse(cr, uid, promo_ids, context=context)]

        return True

    def try_init_next_promotion_dates(self, cr, uid, context=None):
        """Initializes next promotion dates when blank."""

        #Fetch all active employees due for a promotion
        employee_obj = self.pool.get('hr.employee')
        promo_rule_obj = self.pool.get('ng.state.payroll.promotion.rule')
        employee_ids = employee_obj.search(cr, uid, [('active', '=', 'True'), ('next_promotion_date', '=', False)], context=context)        

        emp = None
        for emp_id in employee_ids:
            emp = employee_obj.browse(cr, uid, emp_id, context=context)
            promo_rule_ids = promo_rule_obj.search(cr, uid, [('from_grade_level', '=', emp.grade_level)], context=context)
            if len(promo_rule_ids) == 1:
                promo_rules = promo_rule_obj.browse(cr, uid, promo_rule_ids[0], context=context)
                if emp.last_promotion_date:        
                    next_promo_date = datetime.strptime(emp.last_promotion_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(years=promo_rules.years_due)
                    if next_promo_date <= datetime.date.today():
                        promo_rules2_ids = promo_rule_obj.search(cr, uid, [('from_grade_level', '=', (emp.grade_level + 1))], context=context)
                        if len(promo_rules2_ids) == 1:
                            promo_rules2 = promo_rule_obj.browse(cr, uid, promo_rules2_ids[0], context=context)  
                            end_date = datetime.date.today() + relativedelta(years=promo_rules2.years_due)
                            emp.update(cr, uid, {'next_promotion_date':end_date}, context=context)
        cr.commit()
        return True

    def try_due_promotions(self, cr, uid, context=None):
        """Creates automatic promotions for confirmation."""

        #Fetch all active employees due for a promotion
        today = datetime.now().date()
        employee_obj = self.pool.get('hr.employee')
        promo_rule_obj = self.pool.get('ng.state.payroll.promotion.rule')
        promo_obj = self.pool.get('ng.state.payroll.promotion')
        employee_ids = employee_obj.search(cr, uid, [('active', '=', 'True'), ('next_promotion_date', '<=', today.strftime(DEFAULT_SERVER_DATE_FORMAT))], order='id')        

        for emp in employee_ids:
            promo_rule_ids = promo_rule_obj.search(cr, uid, [('from_grade_level', '=', (emp.grade_level + 1))])
            if len(promo_rule_ids) == 1:
                promo_rules = promo_rule_obj.browse(cr, uid, promo_rule_ids[0], context=context) 
                end_date = datetime.date.today() + relativedelta(years=promo_rules[0].years_due)
                promo_obj.create(cr, uid, {
                    'promotion_rule_id':promo_rules[0].id,
                    'state':'confirm','promotion_type':'auto',
                    'effective_date':today.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'end_date':end_date,
                    'from_pay_category_id':emp.paycategory_id,
                    'from_pay_scheme_id':emp.payscheme_id,
                    'from_grade_level':emp.grade_level,
                    'to_pay_category_id':emp.paycategory_id,
                    'to_pay_scheme_id':emp.payscheme_id,
                    'to_grade_level': (emp.grade_level + 1),
                }, context=context)
                emp.update(cr, uid, {'next_promotion_date':end_date}, context=context)
        cr.commit()
        return True

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        res = {'value': {'from_pay_category_id': False, 'from_pay_scheme_id': False, 'from_grade_level': False}}
        
        if employee_id:
            ee = self.pool.get('hr.employee').browse(
                cr, uid, employee_id, context=context)
            res['value']['from_pay_category_id'] = ee.paycategory_id.id
            res['value']['from_pay_scheme_id'] = ee.payscheme_id.id
            res['value']['from_grade_level'] = ee.grade_level
            res['value']['to_pay_category_id'] = ee.paycategory_id.id
            res['value']['to_pay_scheme_id'] = ee.payscheme_id.id
            res['value']['to_grade_level'] = ee.grade_level

        return res
                    
class ng_state_payroll_promotion_rule(models.Model):
    '''
    Promotion Rule
    '''
    _name = "ng.state.payroll.promotion.rule"
    _description = 'Promotion Rule'
    _columns = {    
        'from_grade_level': fields.selection([
            (1, 'GL-1'),
            (2, 'GL-2'),
            (3, 'GL-3'),
            (4, 'GL-4'),
            (5, 'GL-5'),
            (6, 'GL-6'),
            (7, 'GL-7'),
            (8, 'GL-8'),
            (9, 'GL-9'),
            (10, 'GL-10'),
            (12, 'GL-12'),
            (13, 'GL-13'),
            (14, 'GL-14'),
            (15, 'GL-15'),
            (16, 'GL-16'),
            (17, 'GL-17'),
        ], 'From Grade Level'),
        'to_grade_level': fields.selection([
            (1, 'GL-1'),
            (2, 'GL-2'),
            (3, 'GL-3'),
            (4, 'GL-4'),
            (5, 'GL-5'),
            (6, 'GL-6'),
            (7, 'GL-7'),
            (8, 'GL-8'),
            (9, 'GL-9'),
            (10, 'GL-10'),
            (12, 'GL-12'),
            (13, 'GL-13'),
            (14, 'GL-14'),
            (15, 'GL-15'),
            (16, 'GL-16'),
            (17, 'GL-17'),
        ], 'To Grade Level'),
        'years_due': fields.integer('Due on Years', help='Due on Years'),
    }
    
class ng_state_payroll_disciplinary(models.Model):
    '''
    Payroll Disciplinary (Suspension/Reinstatement)
    '''
    _name = "ng.state.payroll.disciplinary"
    _description = 'Payroll Disciplinary (Suspension/Reinstatement)'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True),
        'action_type': fields.selection([
            ('suspension', 'Suspension'),
            ('reinstatement', 'Reinstatement'),
        ], 'Type', readonly=False),
        'date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'end_date': fields.date('End Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'unpaid_suspension': fields.boolean('Unpaid Suspension', help='If checked, employee is not paid during the suspension period.'),
    }

    _rec_name = 'date'
     
    _defaults = {
        'state': 'draft',
        'action_type': 'suspension',
        'unpaid_suspension': False,
    }
       
    _track = {
        'state': {
            'ng_state_payroll_disciplinary.mt_alert_disc_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'ng_state_payroll_disciplinary.mt_alert_disc_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_disciplinary.mt_alert_disc_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
        employee_obj = self.pool.get('hr.employee')
        data = employee_obj.read(
            cr, uid, employee_id, ['state', 'retirement_due_date'], context=context) 
        if data.get('retirement_due_date', False) and data['retirement_due_date'] != '':
            retirementDate = datetime.strptime(
                data['retirement_due_date'], DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(
                effective_date, DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= retirementDate:
                raise orm.except_orm(
                    _('Warning!'),
                    _('The retirement date is on or before the effective '
                      'date of the transfer.')
                )
                
        return True
    
    def _needaction_domain_get(self, cr, uid, context=None):

        users_obj = self.pool.get('res.users')

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    
    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete Disciplinary action!'),
                    _('Disciplinary action has been initiated. Either cancel the disciplinary action or create another to undo it.')
                )

        return super(ng_state_payroll_disciplinary, self).unlink(cr, uid, ids, context=context)

    def effective_date_in_future(self, cr, uid, ids, context=None):

        today = datetime.now().date()
        for disc in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def disciplinary_state_confirm(self, cr, uid, ids, context=None):
        _logger.info("before state_confirm - %d", uid)
        for disc in self.browse(cr, uid, ids, context=context):
            self._check_state(
                cr, uid, disc.employee_id.id, disc.date, context=context)
            self.write(cr, uid, disc.id, {'state': 'confirm'}, context=context)
        _logger.info("after state_confirm - %d", uid)
        cr.commit()
        return True

    def disciplinary_state_done(self, cr, uid, ids, context=None):

        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, disc.employee_id.id, disc.date,
                    context=context)
                status_obj = self.pool.get('ng.state.payroll.status')
                if disc.action_type == 'suspension':
                    suspended_status_ids = status_obj.search(cr, uid, [('name', '=', 'SUSPENDED')], context=context)
                    employee_obj.write(
                        cr, uid, disc.employee_id.id, {
                            'status_id': suspended_status_ids[0].id},
                        context=context)
                else:
                    suspended_status_ids = status_obj.search(cr, uid, [('name', '=', 'ACTIVE')], context=context)
                    employee_obj.write(
                        cr, uid, disc.employee_id.id, {
                            'status_id': suspended_status_ids[0].id},
                        context=context)
                self.write(
                    cr, uid, disc.id, {'state': 'done'}, context=context)
            else:
                return False

        cr.commit()
        return True

    def try_pending_disciplinary_actions(self, cr, uid, context=None):
        """Completes pending disciplinary actions. Called from
        the scheduler."""

        disc_obj = self.pool.get('ng.state.payroll.disciplinary')
        today = datetime.now().date()
        disc_ids = disc_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'ng.state.payroll.disciplinary', xfer.id, 'signal_done', cr)
         for xfer in self.browse(cr, uid, disc_ids, context=context)]

        return True
   
class ng_state_payroll_demise(models.Model):
    '''
    Payroll Employee Demise
    '''
    _name = "ng.state.payroll.demise"
    _description = 'Payroll Employee Demise'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True),
        'date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }
 
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
    }
       
    _track = {
        'state': {
            'ng_state_payroll_demise.mt_alert_demise_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'ng_state_payroll_demise.mt_alert_demise_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_demise.mt_alert_demise_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
                
        return True
    
    def _needaction_domain_get(self, cr, uid, context=None):
        users_obj = self.pool.get('res.users')
        _logger.info("_needaction_domain_get - %s", users_obj)

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    
    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete Demise action!'),
                    _('Demise action has been initiated. Either cancel the demise action or create another to undo it.')
                )

        return super(ng_state_payroll_demise, self).unlink(cr, uid, ids, context=context)

    def effective_date_in_future(self, cr, uid, ids, context=None):

        today = datetime.now().date()
        for disc in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def demise_state_confirm(self, cr, uid, ids, context=None):
        _logger.info("before state_confirm - %d", uid)
        for disc in self.browse(cr, uid, ids, context=context):
            self._check_state(
                cr, uid, disc.employee_id.id, disc.date, context=context)
            self.write(cr, uid, disc.id, {'state': 'confirm'}, context=context)
        _logger.info("after state_confirm - %d", uid)
        cr.commit()
        return True

    def demise_state_done(self, cr, uid, ids, context=None):

        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, disc.employee_id.id, disc.date,
                    context=context)
                status_obj = self.pool.get('ng.state.payroll.status')
                death_status_ids = status_obj.search(cr, uid, [('name', '=', 'DEATH')], context=context)
                employee_obj.write(
                    cr, uid, disc.employee_id.id, {
                        'status_id': death_status_ids[0].id},
                    context=context)
                self.write(
                    cr, uid, disc.id, {'state': 'done'}, context=context)
            else:
                return False
        cr.commit()
        return True

    def try_pending_demise_actions(self, cr, uid, context=None):
        """Completes pending demise actions. Called from
        the scheduler."""

        disc_obj = self.pool.get('ng.state.payroll.demise')
        today = datetime.now().date()
        disc_ids = disc_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'ng.state.payroll.demise', xfer.id, 'signal_done', cr)
         for xfer in self.browse(cr, uid, disc_ids, context=context)]

        return True
   
class ng_state_payroll_query(models.Model):
    '''
    HR Employee Query
    '''
    _name = "ng.state.payroll.query"
    _description = 'HR Employee Query'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True),
        'date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'title': fields.char('Title', help='Title of the query'),
        'comments': fields.text('Comments', help='Description of the query'),
        'emp_response': fields.text('Response', help='Response to query'),
    }
 
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
    }
       
    _track = {
        'state': {
            'ng_state_payroll_query.mt_alert_query_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'ng_state_payroll_query.mt_alert_query_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_query.mt_alert_query_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
                
        return True
    
    def _needaction_domain_get(self, cr, uid, context=None):
        users_obj = self.pool.get('res.users')
        _logger.info("_needaction_domain_get - %s", users_obj)

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    
    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete query action!'),
                    _('query action has been initiated. Either cancel the query action or create another to undo it.')
                )

        return super(ng_state_payroll_query, self).unlink(cr, uid, ids, context=context)

    def effective_date_in_future(self, cr, uid, ids, context=None):

        today = datetime.now().date()
        for disc in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def query_state_confirm(self, cr, uid, ids, context=None):
        _logger.info("before state_confirm - %d", uid)
        for disc in self.browse(cr, uid, ids, context=context):
            self._check_state(
                cr, uid, disc.employee_id.id, disc.date, context=context)
            self.write(cr, uid, disc.id, {'state': 'confirm'}, context=context)
        _logger.info("after state_confirm - %d", uid)
        cr.commit()
        return True

    def query_state_done(self, cr, uid, ids, context=None):

        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, disc.employee_id.id, disc.date,
                    context=context)
                status_obj = self.pool.get('ng.state.payroll.status')
                death_status_ids = status_obj.search(cr, uid, [('name', '=', 'DEATH')], context=context)
                employee_obj.write(
                    cr, uid, disc.employee_id.id, {
                        'status_id': death_status_ids[0].id},
                    context=context)
                self.write(
                    cr, uid, disc.id, {'state': 'done'}, context=context)
            else:
                return False
        cr.commit()
        return True

    def try_pending_query_actions(self, cr, uid, context=None):
        """Completes pending query actions. Called from
        the scheduler."""

        disc_obj = self.pool.get('ng.state.payroll.query')
        today = datetime.now().date()
        disc_ids = disc_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'ng.state.payroll.query', xfer.id, 'signal_done', cr)
         for xfer in self.browse(cr, uid, disc_ids, context=context)]

        return True
   
class ng_state_payroll_retirement(models.Model):
    '''
    Payroll Employee Retirement
    '''
    _name = "ng.state.payroll.retirement"
    _description = 'Payroll Employee Retirement'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True),
        'retirement_type': fields.selection([
            ('auto', 'Automatic'),
            ('voluntary', 'Voluntary'),
        ], 'Type', readonly=True),           
        'date': fields.date('Effective Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }
 
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
        'retirement_type': 'voluntary'
    }
       
    _track = {
        'state': {
            'ng_state_payroll_retirement.mt_alert_retirement_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'ng_state_payroll_retirement.mt_alert_retirement_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'ng_state_payroll_retirement.mt_alert_retirement_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
                
        return True
    
    def _needaction_domain_get(self, cr, uid, context=None):
        users_obj = self.pool.get('res.users')
        _logger.info("_needaction_domain_get - %s", users_obj)

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    
    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete Promotion!'),
                    _('Retirement process has been initiated. Either cancel the retirement process or create another to undo it.')
                )

        return super(ng_state_payroll_retirement, self).unlink(cr, uid, ids, context=context)

    def effective_date_in_future(self, cr, uid, ids, context=None):

        today = datetime.now().date()
        for disc in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def retirement_state_confirm(self, cr, uid, ids, context=None):
        _logger.info("before state_confirm - %d", uid)
        for disc in self.browse(cr, uid, ids, context=context):
            self._check_state(
                cr, uid, disc.employee_id.id, disc.date, context=context)
            self.write(cr, uid, disc.id, {'state': 'confirm'}, context=context)
        _logger.info("after state_confirm - %d", uid)
        cr.commit()
        return True

    def retirement_state_done(self, cr, uid, ids, context=None):

        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for disc in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, disc.employee_id.id, disc.date,
                    context=context)
                status_obj = self.pool.get('ng.state.payroll.status')
                retirement_status_ids = status_obj.search(cr, uid, [('name', '=', 'RETIRED')], context=context)
                employee_obj.write(
                    cr, uid, disc.employee_id.id, {
                        'status_id': retirement_status_ids[0].id},
                    context=context)
                self.write(
                    cr, uid, disc.id, {'state': 'done'}, context=context)
            else:
                return False
        cr.commit()
        return True

    def try_pending_retirement_actions(self, cr, uid, context=None):
        """Completes pending retirement actions. Called from
        the scheduler."""

        disc_obj = self.pool.get('ng.state.payroll.retirement')
        today = datetime.now().date()
        disc_ids = disc_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'ng.state.payroll.retirement', xfer.id, 'signal_done', cr)
         for xfer in self.browse(cr, uid, disc_ids, context=context)]

        return True
        
class hr_transfer(orm.Model):

    _name = 'hr.department.transfer'
    _description = 'MDA Transfer'

    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _columns = {
        'employee_id': fields.many2one(
            'hr.employee', 'Employee', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date('Effective Date', required=True, readonly=True,
                            states={'draft': [('readonly', False)]}),
        'src_department_id': fields.related(
            'employee_id', 'department_id', type='many2one',
            relation='hr.department', string='From MDA',
            store=True, readonly=True),
        'dst_department_id': fields.related(
            'employee_id', 'department_id', type='many2one',
            relation='hr.department', store=True,
            string='Destination MDA', readonly=False),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
            'State', readonly=True),
    }

    _rec_name = 'date'

    _defaults = {
        'state': 'draft',
    }

    _track = {
        'state': {
            'hr_transfer.mt_alert_xfer_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'hr_transfer.mt_alert_xfer_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'hr_transfer.mt_alert_xfer_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
        },
    }

    def _needaction_domain_get(self, cr, uid, context=None):

        users_obj = self.pool.get('res.users')

        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    
    def unlink(self, cr, uid, ids, context=None):
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise orm.except_orm(
                    _('Unable to Delete Promotion!'),
                    _('Promotion has been initiated. Either cancel the promotion or create another promotion to undo it.')
                )

        return super(hr_transfer, self).unlink(cr, uid, ids, context=context)

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):

        res = {'value': {'src_department_id': False}}

        if employee_id:
            ee = self.pool.get('hr.employee').browse(
                cr, uid, employee_id, context=context)
            res['value']['src_department_id'] = ee.department_id.id

        return res

    def effective_date_in_future(self, cr, uid, ids, context=None):

        today = datetime.now().date()
        for xfer in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(
                xfer.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    def _check_state(self, cr, uid, employee_id, effective_date, context=None):
        _logger.info("_check_state - %d", employee_id)
        employee_obj = self.pool.get('hr.employee')
        data = employee_obj.read(
            cr, uid, employee_id, ['state', 'retirement_due_date'], context=context) 
        if data.get('retirement_due_date', False) and data['retirement_due_date'] != '':
            retirementDate = datetime.strptime(
                data['retirement_due_date'], DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(
                effective_date, DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= retirementDate:
                raise orm.except_orm(
                    _('Warning!'),
                    _('The retirement date is on or before the effective '
                      'date of the transfer.')
                )
                
        return True

    def state_confirm(self, cr, uid, ids, context=None):
        _logger.info("before state_confirm - %d", uid)
        for xfer in self.browse(cr, uid, ids, context=context):
            self._check_state(
                cr, uid, xfer.employee_id.id, xfer.date, context=context)
            self.write(cr, uid, xfer.id, {'state': 'confirm'}, context=context)
        _logger.info("after state_confirm - %d", uid)
        cr.commit()
        return True

    def state_done(self, cr, uid, ids, context=None):

        employee_obj = self.pool.get('hr.employee')
        today = datetime.now().date()

        for xfer in self.browse(cr, uid, ids, context=context):
            if datetime.strptime(
                xfer.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today:
                self._check_state(
                    cr, uid, xfer.src_contract_id.id, xfer.date,
                    context=context)
                employee_obj.write(
                    cr, uid, xfer.employee_id.id, {
                        'department_id': xfer.dst_department_id.id},
                    context=context)
                self.write(
                    cr, uid, xfer.id, {'state': 'done'}, context=context)
            else:
                return False
        cr.commit()
        return True

    def try_pending_department_transfers(self, cr, uid, context=None):
        """Completes pending departmental transfers. Called from
        the scheduler."""

        xfer_obj = self.pool.get('hr.department.transfer')
        today = datetime.now().date()
        xfer_ids = xfer_obj.search(cr, uid, [
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT)),
        ], context=context)

        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(
            uid, 'hr.department.transfer', xfer.id, 'signal_done', cr)
         for xfer in self.browse(cr, uid, xfer_ids, context=context)]

        return True
    