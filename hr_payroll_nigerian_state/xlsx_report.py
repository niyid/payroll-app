from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
import logging

_logger = logging.getLogger(__name__)

class payroll_summary_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, payroll_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '###,###,##0.#0'})
        for payroll_obj in payroll_objs:
            summary_list = payroll_obj.payroll_summary_ids

            sheet = workbook.add_worksheet(payroll_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4,5]
            header = ['Department','Gross Income','Taxable Income','Net Income','PAYE Tax','Leave Allowance']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row = 1    
            for summary_item in summary_list:
                sheet.write_string(row, 0, summary_item['department_id'].name)
                sheet.write_number(row, 1, summary_item['total_gross_income'], money_format)
                sheet.write_number(row, 2, summary_item['total_taxable_income'], money_format)
                sheet.write_number(row, 3, summary_item['total_net_income'], money_format)
                sheet.write_number(row, 4, summary_item['total_paye_tax'], money_format)
                sheet.write_number(row, 5, summary_item['total_leave_allowance'], money_format)
                row += 1
                
            workbook.close()

class payroll_item_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, payroll_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '###,###,##0.#0'})
        for payroll_obj in payroll_objs:
            item_list = payroll_obj.payroll_item_ids

            sheet = workbook.add_worksheet(payroll_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4,5,6]
            header = ['Employee Name','Employee Number','Gross Income','Taxable Income','Net Income','PAYE Tax','Unpaid Balance']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row = 1    
            for payroll_item in item_list:
                sheet.write_string(row, 0, payroll_item['employee_id'].name_related)
                sheet.write_string(row, 1, payroll_item['employee_id'].employee_no)
                sheet.write_number(row, 2, payroll_item['gross_income'], money_format)
                sheet.write_number(row, 3, payroll_item['taxable_income'], money_format)
                sheet.write_number(row, 4, payroll_item['net_income'], money_format)
                sheet.write_number(row, 5, payroll_item['paye_tax'], money_format)
                sheet.write_number(row, 6, payroll_item['balance_income'], money_format)
                row += 1
                
            workbook.close()

class pension_item_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, pension_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '###,###,##0.#0'})
        for pension_obj in pension_objs:
            item_list = pension_obj.pension_item_ids

            sheet = workbook.add_worksheet(pension_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4]
            header = ['Employee Name','Employee Number','Gross Income','Net Income','Unpaid Balance']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row = 1    
            for payroll_item in item_list:
                sheet.write_string(row, 0, payroll_item['employee_id'].name_related)
                sheet.write_string(row, 1, payroll_item['employee_id'].employee_no)
                sheet.write_number(row, 2, payroll_item['gross_income'], money_format)
                sheet.write_number(row, 3, payroll_item['net_income'], money_format)
                sheet.write_number(row, 4, payroll_item['balance_income'], money_format)
                row += 1
                
            workbook.close()
            
class payroll_mda_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, payroll_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '###,###,##0.#0'})
        for payroll_obj in payroll_objs:
            item_list = payroll_obj.payroll_item_ids

            sheet = None
            row = {}    
            for payroll_item in item_list:
                sheet_name = payroll_item['employee_id'].department_id.name[:31]
                sheet = workbook.get_worksheet_by_name(sheet_name)
                if sheet is None:
                    sheet = workbook.add_worksheet(sheet_name)
                    row[sheet_name] = 0
                    indices = [0,1,2,3,4,5,6]
                    header = ['Employee Name','Employee Number','Gross Income','Taxable Income','Net Income','PAYE Tax','Unpaid Balance']
                    for c in indices:
                        sheet.write(row[sheet_name], c, header[c], bold_font)
                    row[sheet_name] = 1
                sheet.write_string(row[sheet_name], 0, payroll_item['employee_id'].name_related)
                sheet.write_string(row[sheet_name], 1, payroll_item['employee_id'].employee_no)
                sheet.write_number(row[sheet_name], 2, payroll_item['gross_income'], money_format)
                sheet.write_number(row[sheet_name], 3, payroll_item['taxable_income'], money_format)
                sheet.write_number(row[sheet_name], 4, payroll_item['net_income'], money_format)
                sheet.write_number(row[sheet_name], 5, payroll_item['paye_tax'], money_format)
                sheet.write_number(row[sheet_name], 6, payroll_item['balance_income'], money_format)
                row[sheet_name] += 1
                
            workbook.close()

class payment_item_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, scenario_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '###,###,##0.#0'})
        for scenario_obj in scenario_objs:
            item_list = scenario_obj.payment_ids

            sheet = workbook.add_worksheet(scenario_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4,5,6]
            header = ['Employee Name','Employee Number','Net Income','Taxable Income','Payment Amount','Payment Balance','Percentage']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row = 1    
            for payment_item in item_list:
                sheet.write_string(row, 0, payment_item['employee_id'].name_related)
                sheet.write_string(row, 1, payment_item['employee_id'].employee_no)
                sheet.write_number(row, 2, payment_item['net_income'], money_format)
                sheet.write_number(row, 4, payment_item['amount'], money_format)
                sheet.write_number(row, 5, payment_item['balance_income'], money_format)
                sheet.write_number(row, 6, payment_item['percentage'], money_format)
                row += 1
                
            workbook.close()

class payment_nibbs_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, scenario_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format_string = {'num_format': '###,###,##0.#0'}
        money_format = workbook.add_format(money_format_string)
        nibbs_money_format = workbook.add_format({'num_format': '###########'})
        for scenario_obj in scenario_objs:
            item_list = scenario_obj.payment_ids

            sheet = workbook.add_worksheet(scenario_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4,5,6]
            header = ['Serial Number','Account Number','Sort Code','Amount','Beneficiary Name','Narration', 'Payer']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row = 1    
            for payment_item in item_list:
                sheet.write_number(row, 0, row)
                sheet.write_string(row, 1, payment_item['employee_id'].bank_account_no)
                sheet.write_string(row, 2, payment_item['employee_id'].bank_id.bic)
                sheet.write_number(row, 3, (payment_item['net_income'] * 100), nibbs_money_format)
                sheet.write_string(row, 4, payment_item['employee_id'].name_related)
                sheet.write_string(row, 5, str(int(payment_item['percentage'])) + "p for " + payment_item['scenario_id'].payroll_id.calendar_id.name)
                sheet.write_string(row, 6, "0000000000")
                row += 1
                
            workbook.close()

class deduction_nibbs_report(ReportXlsx):
    
    def generate_xlsx_report(self, workbook, vals, scenario_objs):
        bold_font = workbook.add_format({'bold': True})
        money_format_string = {'num_format': '###,###,##0.#0'}
        money_format = workbook.add_format(money_format_string)
        nibbs_money_format = workbook.add_format({'num_format': '###########'})
        for scenario_obj in scenario_objs:
            sheet = workbook.add_worksheet(scenario_obj.name[:31])
            row = 0
            indices = [0,1,2,3,4,5,6]
            header = ['Serial Number','Account Number','Sort Code','Amount','Beneficiary Name','Narration', 'Payer']
            for c in indices:
                sheet.write(row, c, header[c], bold_font)
            
            row += 1
            sheet.write_number(row, 0, row)
            sheet.write_string(row, 1, '8000000001')
            sheet.write_string(row, 2, '011000000')
            sheet.write_number(row, 3, (scenario_obj.payroll_id.total_gross_payroll - scenario_obj.payroll_id.total_net_pension - scenario_obj.payroll_id.total_tax_payroll), nibbs_money_format)
            sheet.write_string(row, 4, 'Plateau State Government')
            sheet.write_string(row, 5, 'DEDUCTION ' + scenario_obj.payroll_id.calendar_id.name)
            sheet.write_string(row, 6, '0000000000')
            row += 1   
            #Tax deductions    
            sheet.write_number(row, 0, row)
            sheet.write_string(row, 1, '9000000001')
            sheet.write_string(row, 2, '076000000')
            sheet.write_number(row, 3, scenario_obj.payroll_id.total_tax_payroll, nibbs_money_format)
            sheet.write_string(row, 4, 'Plateau State Government')
            sheet.write_string(row, 5, 'PAYE ' + scenario_obj.payroll_id.calendar_id.name)
            sheet.write_string(row, 6, '0000000000')
                
            workbook.close()            

payroll_summary_report('report.payroll.summary.xlsx',
            'ng.state.payroll.payroll')

payroll_item_report('report.payroll.item.xlsx',
            'ng.state.payroll.payroll')

pension_item_report('report.pension.item.xlsx',
            'ng.state.payroll.payroll')

payroll_mda_report('report.payroll.mda.xlsx',
            'ng.state.payroll.payroll')

payment_item_report('report.payment.item.xlsx',
            'ng.state.payroll.scenario')

payment_nibbs_report('report.payment.nibbs.xlsx',
            'ng.state.payroll.scenario')

deduction_nibbs_report('report.deduction.nibbs.xlsx',
            'ng.state.payroll.scenario')
