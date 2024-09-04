# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import face_recognition
import StringIO
import base64
import numpy
import re
import cv2
import os
import csv
import smtplib
import random
import ast
import sys
import traceback
import requests
import scipy.io.wavfile
import bob.bio.spear.extractor
import bob.bio.spear.preprocessor

from odoo import models, tools, api, fields, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageEnhance
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import Encoders
from email.mime.text import MIMEText
from xlrd import open_workbook
from bob.bio.spear.extractor import Cepstral
from bob.bio.spear.preprocessor import Energy_2Gauss
from os.path import realpath, normpath

_logger = logging.getLogger(__name__)

class AppConfig(models.Model):
    '''
    Application Configuration
    '''
    _name = "imalive.pension.config"
    _description = 'Application Configuration'
    
    active = fields.Boolean('Active', help='Active Status', required=True)
    jitters = fields.Integer(string='Jitters', required=True)
    tolerance = fields.Float(string='Tolerance', digits=(12,6), required=True)
    win_length_ms = fields.Integer(string='CA Window Length', help='The window length of the cepstral analysis in milliseconds', required=True)
    win_shift_ms = fields.Integer(string='CA Window Shift', help='The window shift of the cepstral analysis in milliseconds', required=True)
    n_filters = fields.Integer(string='Filter Bands', help='The number of filter bands', required=True)
    n_ceps = fields.Integer(string='Coefficients', help='The number of cepstral coefficients', required=True)
    f_min = fields.Float(string='Minimum Frequency', help='The minimal frequency of the filter bank', required=True)
    f_max = fields.Integer(string='Maximum Frequency', help='The maximal frequency of the filter bank', required=True)
    delta_win = fields.Integer(string='Delta Value', help='The integer delta value used for computing the first and second order derivatives', required=True)
    pre_emphasis_coef = fields.Float(string='Pre-emphasis Coeff.', help='The coefficient used for the pre-emphasis', required=True)
    dct_norm = fields.Boolean('Coefficients Multiplier', help='A factor by which the cepstral coefficients are multiplied', required=True)
    mel_scale = fields.Boolean('LFCC or MFCC Scale', help='Tell whether cepstral features are extracted on a Linear (LFCC) or Mel (MFCC) scale', required=True)
    max_iterations = fields.Integer(string='Max Iterations', required=True)
    convergence_threshold = fields.Float(string='Convergence Threshold', required=True)
    variance_threshold = fields.Float(string='Variance Threshold', required=True)
    smoothing_window = fields.Integer(string='Smoothing Window', required=True)
    registration_meth = fields.Selection([
            ('default', 'Default'),
            ('internal', 'Internal Database'),
            ('external', 'External Web-service')
        ], string='Registration Method', required=True)
    data_source_internal = fields.Char('Data Source', help='Database & Table name referencing registration data', required=False)
    data_source_external = fields.Char('External Web-service', help='External Web-service URL to access registration data', required=False)
    
    _defaults = {
        'jitters': 20,
        'tolerance': 0.32,
        'win_length_ms': 20,
        'win_shift_ms': 10,
        'n_filters': 24,
        'n_ceps': 19,
        'f_min': 0.0,
        'f_max': 4000,
        'delta_win': 2,
        'pre_emphasis_coef': 1.0,
        'dct_norm': True,
        'mel_scale': True,
        'max_iterations': 10,
        'convergence_threshold': 0.0005,
        'variance_threshold': 0.0005,
        'smoothing_window': 10,
    }
        
class Pensioner(models.Model):

    _name = "hr.employee"
    _inherit = ['hr.employee']
    
    name_related = fields.Char(related='resource_id.name', string="Pensioner Name", readonly=True, store=True)
    active = fields.Boolean('Active', help='Active Status', required=True)
    sinid = fields.Char('Pension Number', help='Pension Identification Number', required=True)
    mobile_phone = fields.Char('Cellphone', help='Pensioner Cellphone', required=True)
    home_phone = fields.Char('Home Phone', help='Home Phone', required=True)
    passphrase = fields.Char('Pass Phrase', help='Pass Phrase', required=False)
    hire_date = fields.Date('Hire Date', help='Date of Hire')
    retirement_date = fields.Date('Retirement Date', help='Retirement-Due Date')
    bank_account_no = fields.Char('Bank Account', help='Bank Account Number', required=True)
    audio_profile = fields.Binary('Audio Profile', help='Audio Profile', required=False)
    title_id = fields.Many2one('res.partner.title', 'Title')
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
    trxs = fields.One2many('imalive.pension.trx', 'pensioner_id', string='Transaction History')
    dds = fields.One2many('imalive.pension.ddebit', 'pensioner_id', string='Direct Debit Instructions')
    payments = fields.One2many('imalive.pension.payment.item', 'pensioner_id', string='Pension Payment History')
    recipients = fields.One2many('imalive.pension.ddebit.recipient', 'pensioner_id', string='My Recipients')
    disabilities = fields.Many2many('imalive.pension.disability', 'rel_pensioner_disability', 'pensioner_id', 'disability_id', 'Disabilities')
    _defaults = {
        'active': False,
    }
    
    _sql_constraints = [
        ('sinid_uniq', 'unique(sinid)', 'Duplicates not allowed for PIN'),
    ]
      
    @api.model
    def update_profile(self, pensioner_id, vals, context=None):
        _logger.info("Calling update_profile - %d", pensioner_id)
        
        if self.env.user.id and pensioner_id:
            pensioner_data = self.env['hr.employee'].search([('id', '=', pensioner_id)])
            
            if pensioner_data:
                pensioner_data.update(vals)
            else:
                return "No pensioner found: " + str(pensioner_id)
        else:
            return "Pensioner ID is required"
        
        return pensioner_id
              
    @api.model
    def fetch_profile(self, pensioner_id, context=None):
        _logger.info("Calling fetch_profile - %d", pensioner_id)
        
        pensioner_dict = {}
        if self.env.user.id and pensioner_id:
            pensioner_data = self.env['hr.employee'].search([('id', '=', pensioner_id)])
            if pensioner_data:
                pensioner_dict['sinid'] = pensioner_data.sinid
                pensioner_dict['mobile_phone'] = pensioner_data.mobile_phone
                pensioner_dict['home_phone'] = pensioner_data.home_phone
                pensioner_dict['name_related'] = pensioner_data.name_related
                pensioner_dict['bank_account_no'] = pensioner_data.bank_account_no
                pensioner_dict['bank_id'] = pensioner_data.bank_id.id
                if pensioner_data.title_id:
                    pensioner_dict['title_id'] = pensioner_data.title_id.id
                if pensioner_data.gender:
                    pensioner_dict['gender'] = pensioner_data.gender
                if pensioner_data.birthday:
                    pensioner_dict['birthday'] = pensioner_data.birthday
                if pensioner_data.disabilities:
                    pensioner_dict['disabilities'] = str(pensioner_data.disabilities)
            else:
                return "No pensioner found: " + str(pensioner_id)
        else:
            return "Pensioner ID is required"
            
        return pensioner_dict
                         
    @api.model
    def list_payslip_items(self, pensioner_id, context=None):
        _logger.info("list_payslip_items - %s", pensioner_id)
        #model_singleton = self.env['imalive.pension.' + model_suffix]
        self.env.cr.execute("select name,amount from imalive_pension_payment_item where active='t' and pensioner_id=" + str(pensioner_id))
        item_lines = self.env.cr.fetchall()
        return item_lines
             
    @api.model
    def list_recipient_items(self, vals, context=None):
        _logger.info("list_recipient_items - %s", vals)
        self.env.cr.execute("select id,name from " + vals['table_name'] + " where active='t' and " + vals['field_name'] + " is null or " + vals['field_name'] + "=" + str(vals['field_value']))
        item_lines = self.env.cr.fetchall()
        return item_lines
             
    @api.model
    def list_items(self, model_table, context=None):
        _logger.info("list_items - %s", model_table)
        #model_singleton = self.env['imalive.pension.' + model_suffix]
        
        self.env.cr.execute("select attname from pg_attribute where attrelid = (select oid from pg_class where relname = '" + model_table + "') AND attname = 'active'")
        has_active = self.env.cr.fetchall()
        
        suffix = ""
        if has_active:
            suffix = " where active='t'"
        self.env.cr.execute("select id,name from " + model_table + suffix)
        item_lines = self.env.cr.fetchall()
        return item_lines
                       
    @api.model
    def list_pensioner_items(self, pensioner_id, model_table, context=None):
        _logger.info("list_pensioner_items - %s, %s", pensioner_id, model_table)
        self.env.cr.execute("select id,name from " + model_table + " where pensioner_id is null or pensioner_id=" + str(pensioner_id))
        item_lines = self.env.cr.fetchall()
        return item_lines
                    
    @api.model
    def list_slave_items(self, vals, context=None):
        _logger.info("list_service_items - %s", vals)
        self.env.cr.execute("select id,name from " + vals['table_name'] + " where " + vals['field_name'] + "=" + str(vals['field_value']))
        item_lines = self.env.cr.fetchall()
        return item_lines
                   
    @api.model
    def list_pensioner_ddebit_instructions(self, pensioner_id, context=None):
        _logger.info("list_pensioner_ddebit_instructions - %s", pensioner_id)
        self.env.cr.execute("select id,name,amount from imalive_pension_ddebit where state='approved' and pensioner_id=" + str(pensioner_id))
        item_lines = self.env.cr.fetchall()
        return item_lines
    
    @api.model
    def add_pensioner(self, vals):
        _logger.info("add_pensioner - %s, %s", vals.get('name_related'), vals.get('disability_ids'))
        
        config_singleton = self.env['imalive.pension.config']
        pensioner_singleton = self.env['hr.employee']
        config_instance = config_singleton.search([('active', '=', True)])
        
        pensioner_instance = pensioner_singleton.search([('sinid', '=', str(vals.get('sinid')))])
        if pensioner_instance:
            return "Pension Identification Number '" + vals.get('sinid') + "' already registered"
        
        face_register = base64.b64decode(vals.get('image'))
        rand_num = random.randint(10000000, 1000000000)
        file_name_register = "/tmp/image" + str(rand_num) + ".png"
        image_file_register = open(file_name_register, "wb")
        image_file_register.write(face_register)
        image_file_register.close()
        
        image_register = face_recognition.load_image_file(file_name_register)            
        register_face_encoding = face_recognition.face_encodings(image_register, num_jitters=config_instance[0].jitters)
        
        disability_ids = False
        if vals.get('disability_ids'):
            disability_ids = ast.literal_eval(vals.pop('disability_ids'))
            for d in disability_ids:
                _logger.info("Checking disability ids - %d", d)
        _logger.info("create - disabilities - %s", disability_ids)
        if len(register_face_encoding) == 0:
            return "Poor photo quality. Please recapture."
        else:
            _logger.info("Creating resource...")
            resource_singleton = self.env['resource.resource']
            resource_id = resource_singleton.create({'name':vals.get('name_related'),'active':True,'time_efficiency':100.0,'company_id':1,'resource_type':'user'})
            _logger.info("create - resource_id - %s", resource_id)
            _logger.info("create - updating vals- %d", resource_id.id)
            vals['resource_id'] = resource_id.id
            vals['active'] = False
            vals['color'] = False
            vals['mobile_phone'] = str(vals['mobile_phone'])
            vals['bank_account_no'] = str(vals['bank_account_no'])
            _logger.info("create - pensioner...")
            pensioner_id = self.create(vals)
            enrollment_singleton = self.env['imalive.pension.enrollment']
            _logger.info("Created new pensioner - %d", pensioner_id)
            if pensioner_id:
                if disability_ids:
                    _logger.info("updated disabilities - %s", disability_ids)
                    pensioner_id.write({'disabilities': [(4, disability_id) for disability_id in disability_ids]})
                enrollment_id = enrollment_singleton.create({'pensioner_id':pensioner_id.id,'date':date.today()})
                _logger.info("Created new enrollment - %d", enrollment_id)
                enrollment_singleton.write({'id': enrollment_id.id, 'state':'confirm'})
                _logger.info("Began enrollment process for pensioner - %d", pensioner_id.id)
            
                message = "Dear Sir,\nA new pensioner has been enrolled:\n\n" + "NAME: " + vals.get('name_related') + "\nPHONE: " + vals.get('mobile_phone')+ "\nPENSION NO: " + vals.get('sinid')  + ".\n\nThank you.\n"
                smtp_obj = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
                smtp_obj.ehlo()
                #smtp_obj.starttls()
                #smtp_obj.ehlo()
                smtp_obj.login('osun.payroll@gmail.com', 'p@55w0rd1939')
                sender = 'osun.payroll@gmail.com'
                receivers = ['neeyeed@gmail.com','bjolaosho@chams.com'] #Comma separated email addresses
                msg = MIMEMultipart()
                msg['Subject'] = 'New Pensioner Enrollment' 
                msg['From'] = sender
                msg['To'] = ', '.join(receivers)
                msg.attach(MIMEText(message))
                                                        
                smtp_obj.sendmail(sender, receivers, msg.as_string())         
                _logger.info("Email successfully sent to: " + msg['To'])
                                 
            return pensioner_id.id

    @api.model
    def login(self, pin, face_unknown_base64, context=None):
        _logger.info("Calling login - %d", self.env.user.id)
        _logger.info("Pensioner ID - %s", pin)
        #employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        
        #TODO return the name of the pensioner for display purposes, along with ID
        pensioner_data = []
        if self.env.user.id and pin:
            pensioner_data = self.env['hr.employee'].search([('active', '=', True), ('sinid', '=', str(pin))])
            if pensioner_data:
                if len(pensioner_data) > 1:
                    return "More than one pensioner found with Pension Identification Number '" + pin + "'"
            if pensioner_data:
                p_first_rec = pensioner_data[0]
                _logger.info("Employee ID=%d", p_first_rec.id)
                if p_first_rec.image:
                    return self.match_face(p_first_rec.id, face_unknown_base64, context)
                else:
                    return "No records on file to match. Contact Administrator."
            else:
                _logger.info("No matching pensioner found for PIN or pensioner requires approval. %s", pin)
                return "Pensioner with PIN does not exist or pensioner requires approval."
        else:
            _logger.info("No PIN supplied - %s", pin)
            return "No PIN supplied."

    @api.model
    def login_voice(self, pin, voice_unknown_base64, context=None):
        _logger.info("Calling login - %d", self.env.user.id)
        _logger.info("Pensioner ID - %s", pin)
        #employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
         
        #TODO return the name of the pensioner for display purposes, along with ID
        pensioner_data = []
        if self.env.user.id and pin:
            pensioner_data = self.env['hr.employee'].search([('active', '=', True), ('sinid', '=', str(pin))])
            if pensioner_data:
                if len(pensioner_data) > 1:
                    return "More than one pensioner found with Pension Identification Number '" + pin + "'"
                p_first_rec = pensioner_data[0]
                _logger.info("Employee ID=%d", p_first_rec.id)
                if p_first_rec.image:
                    return self.match_voice(p_first_rec.id, voice_unknown_base64, context)
                else:
                    return "No records on file to match. Contact Administrator."
            else:
                _logger.info("No matching pensioner found for PIN %s", pin)
                return "Pensioner with PIN does not exist."
        else:
            _logger.info("No matching pensioner found for PIN %s", pin)
            return "No Pension Identification Number supplied."

    def get_images_and_labels(self, pensioner_id, image_path, face_cascade):
        _logger.info("Calling get_images_and_labels - %d, %s", pensioner_id, image_path)
        # Read the image and convert to grayscale
#         image_pil = Image.open(image_path).convert('L')
#         image_pil.load()
#         # Convert the image format into numpy array
#         image = numpy.array(image_pil, 'uint8')
#         _logger.info("Image dimension - %s", image.shape)
        img = cv2.imread(image_path)
        # Detect the face in the image
        # If face is detected, append the face to images and the label to labels
        images = [img, img]
        labels = [pensioner_id, pensioner_id]
        (images, labels) = [numpy.array(lis) for lis in [images, labels]]

        return images, labels
       
    @api.model
    def match_face(self, pensioner_id, face_unknown_base64, context=None):
        _logger.info("Calling match_face - %d", self.env.user.id)
        
        config_singleton = self.env['imalive.pension.config']
        config_instance = config_singleton.search([('active', '=', True)])
        
        if self.env.user.id and face_unknown_base64 and pensioner_id:
            pensioner_data = self.env['hr.employee'].search([('id', '=', pensioner_id),('active', '=', True)])
            
            _logger.info("Found Pensioner(s):%d", len(pensioner_data))
            
            rand_num = random.randint(10000000, 1000000000)
            face_unknown = base64.urlsafe_b64decode(face_unknown_base64)
            file_name_unknown = "/tmp/image" + str(rand_num) + ".png"
            image_file_unknown = open(file_name_unknown, "wb")
            image_file_unknown.write(face_unknown)
            image_file_unknown.close()

            image_unknown = face_recognition.load_image_file(file_name_unknown)            
            unknown_face_encoding = face_recognition.face_encodings(image_unknown, num_jitters=config_instance[0].jitters)
            _logger.info("unknown_face_encoding=%d", len(unknown_face_encoding))
            if len(unknown_face_encoding) == 0:
                _logger.info("Enhancing...")
                file_name_unknown_enhanced = "/tmp/image" + str(rand_num) + "_enhanced.png"
                #Try again after making image brighter
                enhancer = ImageEnhance.Sharpness(Image.open(file_name_unknown))
                enhancer.enhance(4).save(file_name_unknown_enhanced, quality=100)
                
                enhancer = ImageEnhance.Brightness(Image.open(file_name_unknown_enhanced))
                enhancer.enhance(2).save(file_name_unknown_enhanced, quality=100)
#                 image_stream_unknown = Image.open(file_name_unknown)
#                 image_file_unknown_brighter = image_stream_unknown.point(lambda p: p * 1.5)
#                 image_file_unknown_brighter.save(file_name_unknown_sharpen, "PNG")
                image_unknown = face_recognition.load_image_file(file_name_unknown_enhanced)            
                unknown_face_encoding = face_recognition.face_encodings(image_unknown, num_jitters=config_instance[0].jitters)
                _logger.info("unknown_face_encoding=%d", len(unknown_face_encoding))
                if len(unknown_face_encoding) == 0:
                    return "Poor photo quality. Please recapture."
            if not pensioner_data:
                return "No pensioner with id " + pensioner_id + " found"
            if len(pensioner_data) == 1:
                for p in pensioner_data:
                    if p.image:
                        image_stream = Image.open(StringIO.StringIO(p.image.decode('base64')))
                        
                        file_name_known = "/tmp/image" + str(pensioner_id) + ".png"
                        image_stream.save(file_name_known, "PNG")
                        image_known = face_recognition.load_image_file(file_name_known)            
                        known_face_encoding = face_recognition.face_encodings(image_known, num_jitters=config_instance[0].jitters)
                        _logger.info("face_encoding=%d", len(known_face_encoding))
                        if known_face_encoding and unknown_face_encoding:
                            results = face_recognition.compare_faces([known_face_encoding[0]], unknown_face_encoding[0], tolerance=config_instance[0].tolerance)
                            _logger.info("results=%d", len(results))
                            if results[0]:
                                _logger.info("Pensioner Found: %d", pensioner_id)
                                return pensioner_id
                            else:
                                _logger.info("No pensioner Found: %d", pensioner_id)
                                return "We were unable to fully match your face with the photo on file; please try again (To improve the photo quality, you may improve the lighting conditions and do not make any sudden movements)."
                        else:
                            _logger.info("No Pensioner(s) Found: %d", pensioner_id)
                            return "You require a photo on file and a new photo to match with."
            else:
                return "More than one pensioners found with id " + pensioner_id
        else:
            _logger.info("No matching pensioner found for ID %d", self.env.user.id)

    @api.model
    def process_voice(self, voice_base64, context=None):
        _logger.info("Processing voice..")
             
        config_singleton = self.env['imalive.pension.config']
        config_instance = config_singleton.search([('active', '=', True)])

        rand_num = random.randint(10000000, 1000000000)
        voice = base64.urlsafe_b64decode(voice_base64)
        file_name_voice = "/tmp/voice" + str(rand_num) + ".wav"
        voice_file = open(file_name_voice, "wb")
        voice_file.write(voice)
        voice_file.close()
        
        rate_wavesample = []
        rate, energy_signal = scipy.io.wavfile.read(file_name_voice)
        _logger.info("energy_signal=%s", energy_signal)
        energy_signal = numpy.cast['float'](energy_signal)
        energy_signal = energy_signal.flatten()
        _logger.info("energy_signal (flatten)=%s", energy_signal.flatten())
        _logger.info("energy_signal (reshape)=%s", numpy.reshape(energy_signal, numpy.product(energy_signal.shape)))
    
        rate_wavesample.append(rate)
        rate_wavesample.append(energy_signal)
                    
        # populate Preprocessor with parameters
        preprocessor = Energy_2Gauss()
        processed_data = preprocessor(rate_wavesample)
            
        _logger.info("Signal Rate=%d", rate)
        _logger.info("Signal Length=%d", len(energy_signal))
        _logger.info("Signal Duration=%d", len(energy_signal)/rate)
            
        _logger.info("Processed Rate=%d", processed_data[0])
        _logger.info("Processed Data Length=%d", len(processed_data[1]))
        _logger.info("Processed Label Length=%d", len(processed_data[2]))
        
        return processed_data[2]
#     
#         cepstral = Cepstral(rate, 
#                        config_instance.win_length_ms, 
#                        config_instance.win_shift_ms, 
#                        config_instance.n_filters, 
#                        config_instance.n_ceps, 
#                        config_instance.f_min, 
#                        config_instance.f_max, 
#                        config_instance.delta_win, 
#                        config_instance.pre_emphasis_coef, 
#                        config_instance.mel_scale, 
#                        config_instance.dct_norm)
        
#             mfcc = cepstral(preprocessed_data)
#             _logger.info("MFCC Total Length=%d", len(mfcc))
#             _logger.info("MFCC Length=%d", len(mfcc[0]))
#             _logger.info("MFCC=%s", mfcc[0])
#              
#             cepstral.mel_scale = False
#             lfcc = cepstral(preprocessed_data)
#             _logger.info("LFCC Total Length=%d", len(lfcc))
#             _logger.info("LFCC Length=%d", len(lfcc[0]))
#             _logger.info("LFCC=%s", lfcc[0])
#              
#             cepstral.with_energy = True
#             lfcc_e = cepstral(preprocessed_data)
#             _logger.info("LFCC Total Energy Length=%s", len(lfcc_e))
#             _logger.info("LFCC Energy Length=%s", len(lfcc_e[0]))
#             _logger.info("LFCC DD=%s", lfcc_e[0])
#              
#             cepstral.with_delta = True
#             cepstral.with_delta_delta = True
#             lfcc_e_d_dd = cepstral(preprocessed_data)
#             _logger.info("LFCC Total DD Length=%s", len(lfcc_e_d_dd))
#             _logger.info("LFCC DD Length=%s", len(lfcc_e_d_dd[0]))
#             _logger.info("LFCC DD=%s", lfcc_e_d_dd[0])
       
    @api.model
    def register_voice(self, pensioner_id, passphrase, voice_base64, context=None):
        _logger.info("Calling register_voice - %d (%s)", pensioner_id, passphrase)
         
        if self.env.user.id and voice_base64 and pensioner_id:
            pensioner_data = self.env['hr.employee'].search([('id', '=', pensioner_id)])
             
            _logger.info("Found Pensioner(s):%d", len(pensioner_data))
             
            #TODO Store Voice profile in Pensioner
            processed_voice = self.process_voice(voice_base64, context)
            
            #processed_voice_b64 = base64.b64encode(processed_voice)
            numpy.save('/tmp/' + str(pensioner_id) + '.npy', processed_voice)
             
            #Update passphrase
            pensioner_data.update({'passphrase':passphrase})
            return True
        
        return False
        
    @api.model
    def match_voice(self, pensioner_id, voice_unknown_base64, context=None):
        _logger.info("match_voice: %d", pensioner_id)
        #TODO Get processed data from Pensioner
        #pensioner_data = self.env['hr.employee'].search([('id', '=', pensioner_id)])
        processed_voice = self.process_voice(voice_unknown_base64, context)
        #profile_processed_voice = base64.b64decode(pensioner_data.audio_profile)
        profile_processed_voice = numpy.load('/tmp/' + str(pensioner_id) + '.npy')
        if len(processed_voice) < len(profile_processed_voice):
            profile_processed_voice = profile_processed_voice[:len(processed_voice)]
        
        if len(profile_processed_voice) < len(processed_voice):
            processed_voice = processed_voice[:len(profile_processed_voice)]
        
        _logger.info("match_voice len compare: %d, %d", len(profile_processed_voice), len(processed_voice))
        match = numpy.allclose(processed_voice, profile_processed_voice, atol=1e-2)
        
        if match:
            return pensioner_id
        else:
            return "No matching pensioner found."
       
    @api.model
    def activate_payment(self, pensioner_id, payment_code, face_unknown_base64, context=None):
        _logger.info("Calling activate_payment - %d, %s", pensioner_id, payment_code)
        pensioner_check_id = self.match_face(pensioner_id, face_unknown_base64, context)
        payment_item_singleton = self.env['imalive.pension.payment.item']
        employee_singleton = self.env['hr.employee']
        if isinstance(pensioner_check_id, (int, long)):
            #Use paymentCode to find payment item and approve accordingly
            payment_items = payment_item_singleton.search([('pensioner_id.id', '=', pensioner_id), ('active', '=', False), ('payment_code', '=', payment_code)])
            if payment_items:
                for p in payment_items:
                    payment_items.write({'id':p.id, 'active': True}) #Activate inactive payment with pensioner_id and payment_code
                    employee_obj = employee_singleton.search([('id', '=', pensioner_id)])
                    if employee_obj.work_email:
                        message = "Dear Sir,\nYour pension with details as shown below has been approved for payment:\n\n CALENDAR: " + p.payment_id.calendar_id.name + "\nNARRATION: " + p.name + "\nAMOUNT: " + 'NGN{:,.2f}'.format(p.amount) + ".\n\nThank you.\n"
                        smtp_obj = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
                        smtp_obj.ehlo()
                        #smtp_obj.starttls()
                        #smtp_obj.ehlo()
                        smtp_obj.login(user="osun.payroll@gmail.com", password="p@55w0rd1939")
                        sender = 'osun.payroll@gmail.com'
                        receivers = [employee_obj.work_email] #Comma separated email addresses
                        msg = MIMEMultipart()
                        msg['Subject'] = 'Payment Approved' 
                        msg['From'] = sender
                        msg['To'] = ', '.join(receivers)
                        msg.attach(MIMEText(message))
                                                                
                        smtp_obj.sendmail(sender, receivers, msg.as_string())
                        _logger.info("Email successfully sent to: " + msg['To'])         
                _logger.info("Activated pending payment - %d", pensioner_id)
                
            else:
                return "No payments to activate or invalid payment code"
        else:
            return "No pensioner found"
        return pensioner_check_id
        
class PayCalendar(models.Model):
    '''
    Pay Calendar
    '''
    _name = "imalive.pension.calendar"
    _description = 'Pay Calendar'

    name = fields.Char('Name', help='Calendar Name', required=False)
    pay_freq = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], 'Scheduled Pay', required=True, select=True)
    from_date = fields.Date('From Date', help='From Date', required=True)
    to_date = fields.Date('To Date', help='To Date', required=True)
                        
class PensionTransaction(models.Model):

    _name = "imalive.pension.trx"
    _description = "Pensioner Transaction"

    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string='Amount', required=True)
    trx_type = fields.Selection([
            ('debit', 'Debit'),
            ('credit', 'Credit')
        ], string='Transaction Type', required=True, readonly=True)
    pensioner_id = fields.Many2one('hr.employee', string='Pensioner', required=True, track_visibility='onchange')
                        
class DdRecipient(models.Model):

    _name = "imalive.pension.ddebit.recipient"
    _description = "Direct Debit Recipient"

    name = fields.Char('Name', help='Name of Business')
    bank_account_no = fields.Char('Bank Account', help='Bank Account Number')
    bank_id = fields.Many2one('res.bank', string='Bank')
    active = fields.Boolean('Active', help='Active Status', required=True)
    dd_services = fields.One2many('imalive.pension.ddebit.service', 'recipient_id', string='Direct Debit Services')
    pensioner_id = fields.Many2one('hr.employee', string='Owner', required=False, track_visibility='onchange')
    _defaults = {
        'active': True,
    }
    
    @api.model
    def create(self, vals):
        _logger.info("create - %s", vals)
        vals['active'] = True
        return super(DdRecipient, self).create(vals)
                                    
class DdService(models.Model):

    _name = "imalive.pension.ddebit.service"
    _description = "Direct Debit Service"

    name = fields.Char(string='Name', required=True)
    amount = fields.Float(string='Amount', required=True)
    active = fields.Boolean('Active', help='Active Status', required=True)
    recipient_id = fields.Many2one('imalive.pension.ddebit.recipient', string='Recipient', required=True, track_visibility='onchange') 
   
    _defaults = {
        'active': True,
    }                            
                            
class DirectDebit(models.Model):

    _name = "imalive.pension.ddebit"
    _description = "Direct Debit Instruction"

    name = fields.Char(string='Narration', required=True)
    amount = fields.Float(string='Amount', required=False)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True)
    recurrent = fields.Boolean('Recurrent', help='Recurrent', required=True)
    pensioner_id = fields.Many2one('hr.employee', string='Pensioner', required=True, track_visibility='onchange')     
    recipient_id = fields.Many2one('imalive.pension.ddebit.recipient', string='Recipient', required=True, track_visibility='onchange')
    service_id = fields.Many2one('imalive.pension.ddebit.service', string='Service', required=False, track_visibility='onchange') 
    calendar_id = fields.Many2one('imalive.pension.calendar', 'First Calendar', track_visibility='onchange', required=True)

    _defaults = {
        'state': 'draft',
    }
   
    _track = {
        'state': {
            'imalive_pension_ddebit.mt_alert_ddebit_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'imalive_pension_ddebit.mt_alert_ddebit_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'imalive_pension_ddebit.mt_alert_ddebit_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approved',
        },
    }
    
    @api.model
    def create(self, vals):
        _logger.info("create - %s", vals)
        vals['state'] = 'draft'
        if vals.get('service_id'):
            service_data = self.env['imalive.pension.ddebit.service'].search([('id', '=', vals.get('service_id'))])
            vals['amount'] = service_data.amount
            
        return super(DirectDebit, self).create(vals)
        
    @api.onchange('pensioner_id')
    def dd_recipient_list_update(self):
        return {'domain': {'recipient_id': ['|',('pensioner_id','=',self.pensioner_id.id), ('pensioner_id','=',False)] }}

    @api.onchange('recipient_id')
    def dd_service_list_update(self):
        return {'domain': {'service_id': [('recipient_id','=',self.recipient_id.id)] }}

    @api.onchange('service_id')
    def dd_amount_update(self):
        if self.service_id:
            self.amount = self.service_id.amount

    @api.model
    def _check_state(self,pensioner_id, context=None):
        _logger.info("_check_state - %d", pensioner_id)
                
        return True
    
    @api.model
    def _needaction_domain_get(self, context=None):
        users_singleton = self.env['res.users']
        users_obj = self.pool.get('res.users')
        _logger.info("_needaction_domain_get - %s", users_obj)
        
        if self.env.user.has_group('im_alive_pension.group_pension_administrator'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False
    
    @api.multi
    def unlink(self, context=None):
        for item_obj in self.browse(context=context):
            if item_obj.state not in ['draft']:
                raise exceptions.except_orm(
                    _('Unable to Delete Payment Upload action!'),
                    _('Payment Upload action has been initiated. Either cancel the action or create another to undo it.')
                )

        return super(DirectDebit, self).unlink()

    @api.multi
    def effective_date_in_future(self, context=None):

        today = datetime.now().date()
        for disc in self.browse(context=context):
            effective_date = datetime.strptime(
                disc.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    @api.multi
    def ddebit_state_confirm(self, context=None):
        _logger.info("ddebit_state_confirm - %d", self.env.user.id)
        self.write({'state':'confirm'})
        return True

    @api.multi
    def ddebit_state_cancel(self, context=None):
        _logger.info("ddebit_state_cancel - %d", self.env.user.id)
        self.write({'state':'cancel'})
        return True

    @api.multi
    def ddebit_state_done(self, ddebit_ids, context=None):
        for o in self.browse(ddebit_ids):
            if o.state == 'confirm':
                #TODO If third approved ddebit, initiate termination process
                #self.write({'id':o.id, 'state': 'approved'})
                self.env.cr.execute("update imalive_pension_ddebit set state='approved' where id=(" + str(o.id) + ")")
            else:
                return False
        return True

    @api.multi
    def try_pending_ddebit_actions(self, context=None):
        """Completes pending Direct Debit actions. Called from
        the scheduler."""
        
        _logger.info("Running try_pending_ddebit_actions cron-job...")

        ddebit_obj = self.env['imalive.pension.ddebit']
        ddebit_ids = ddebit_obj.search([
            ('state', '=', 'confirm'),
        ])

        self.ddebit_state_done(ddebit_ids.ids)

        return True
                            
class PaymentItem(models.Model):

    _name = "imalive.pension.payment.item"
    _description = "Payment Item"

    name = fields.Char(string='Narration', required=True)
    amount = fields.Float(string='Amount', required=True)
    pensioner_id = fields.Many2one('hr.employee', string='Pensioner', required=True) 
    payment_id = fields.Many2one('imalive.pension.payment', string='Payment Upload', required=True)
    payment_code = fields.Char(string='Payment Code', required=True)
    active = fields.Boolean('Active', help='Active Status', required=True) 

class PaymentInstruction(models.Model):
    '''
    Payment Instruction
    '''
    _name = "imalive.pension.payment"
    _description = 'Payment Instruction'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    name = fields.Char(string='Name', required=True)
    upload_file = fields.Binary('Payment File', required=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('approved', 'Approved'),
            ('closed', 'Closed'),
            ('cancel', 'Cancelled'),
        ], 'State', required=False, readonly=True)
    date = fields.Date('Effective Date', required=True, states={'draft': [('readonly', False)]})
    calendar_id = fields.Many2one('imalive.pension.calendar', 'Calendar', track_visibility='onchange', required=True)
    notify_emails = fields.Char('Notify Email', help='Comma separated email recipients for event notification', required=True)
    payment_item_ids = fields.One2many('imalive.pension.payment.item','payment_id','Payment Items')
 
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
        'date': date.today(),
    }
       
    _track = {
        'state': {
            'imalive_pension_earnded_upload.mt_alert_earnded_upload_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'imalive_pension_earnded_upload.mt_alert_earnded_upload_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approved',
        },
    }
    
    @api.multi
    def try_payment(self, context=None):
        _logger.info("try_payment - %d", self.env.user.id)
        #Use the payment_item_ids to create a NIBBS payment file and send to NIBBS
    
    @api.model
    def _needaction_domain_get(self, context=None):
        users_obj = self.env['res.users']
        _logger.info("_needaction_domain_get - %s", users_obj)

        if self.env.user.has_group('im_alive_pension.group_pension_administrator'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False

    @api.multi
    def unlink(self, context=None):
        for item_obj in self.browse(self.ids):
            if item_obj.state not in ['draft']:
                raise exceptions.except_orm(
                    _('Unable to Delete Payment Upload action!'),
                    _('Payment Upload action has been initiated. Either cancel the action or create another to undo it.')
                )

        return super(PaymentInstruction, self).unlink()

    @api.multi
    def effective_date_in_future(self, context=None):
        today = datetime.now().date()
        for o in self.browse(self.ids):
            effective_date = datetime.strptime(
                o.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    @api.multi
    def close(self, context=None):
        #TODO Process file, select distinct by name and create templates for earnings/deductions
        _logger.info("before state_close - %d", self.env.user.id)
        for payment_id in self.ids:
            self.write({'id':payment_id, 'state': 'closed'})
            _logger.info("after state_close - %d", self.env.user.id)
        return True

    @api.multi
    def payment_state_confirm(self, context=None):
        #TODO Process file, select distinct by name and create templates for earnings/deductions
        _logger.info("before state_confirm - %d", self.env.user.id)
        for payment_id in self.ids:
            self.write({'id':payment_id, 'state': 'confirm'})
            _logger.info("after state_confirm - %d", self.env.user.id)
        return True

    @api.multi
    def try_confirmed_payment_actions(self, context=None):
        _logger.info("Running try_confirmed_payment_actions cron-job...")
        upload_obj = self.env['imalive.pension.payment']
        pensioner_obj = self.env['hr.employee']
        today = datetime.now().date()

        self.env.cr.execute('deallocate all');
        self.env.cr.execute('prepare insert_payment (int,int,text,text,numeric,timestamp,timestamp,int,int,bool) as insert into imalive_pension_payment_item (pensioner_id,payment_id,payment_code,name,amount,create_date,write_date,create_uid,write_uid,active) values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) returning id')            

        upload_ids = upload_obj.search([('state', '=', 'confirm')])
        
        smtp_obj = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
        smtp_obj.ehlo()
        smtp_obj.login(user="osun.payroll@gmail.com", password="p@55w0rd1939")
        sender = 'osun.payroll@gmail.com'
        #Spreadsheet format: pin,narration,amount
        for upload in upload_ids:
            if datetime.strptime(upload.date, DEFAULT_SERVER_DATE_FORMAT).date() <= today and upload.state == 'confirm':
                exception_list = []
                data_file = base64.decodestring(upload.upload_file)
                wb = open_workbook(file_contents=data_file)
                for s in wb.sheets():
                    _logger.info("Number of sheets: %d", len(wb.sheets()))
                    _logger.info("Number of records: %d", s.nrows)
                    sin_id = False
                    for row in range(s.nrows):
                        exec_inserts = False
                        if row > 0: #Skip first row
                            data_row = []
                            for col in range(s.ncols):
                                value = (s.cell(row, col).value)
                                data_row.append(value)
                            pensioner = False
                            if len(data_row) == 3:
                                sin_id = str(data_row[0]).strip()
                                if sin_id.endswith('.0'):
                                    sin_id = sin_id[:-2]
                                _logger.info("Searching for pensioner with sinid=%s", sin_id)
                                pensioner = pensioner_obj.search([('sinid', '=', sin_id)])
                            
                                if len(pensioner) == 0:
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'No pensioner found - ' + str(data_row[0])})
                                elif len(pensioner) > 1:
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'Non-unique - ' + str(data_row[0])})
                                elif data_row[2] <= 0: #Negative or zero value throws exception
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'Negative amount for - ' + str(data_row[0])})
                                elif not data_row[0]: #PIN blank
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'Pensioner ID cannot be blank for row'})
                                elif not data_row[1]: #Narration blank
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'Narration cannot be blank for row'})
                                elif not data_row[2]: #Amount blank
                                    exception_list.append({'pin':data_row[0],'narration':data_row[1],'amount':data_row[2],'error':'Amount is required'})
                                else:
                                    exec_inserts = True
                                if exec_inserts:
                                    payment_code = str(random.randint(10000, 999999)).zfill(6)
                                    self.env.cr.execute('execute insert_payment(%s,%s,%s,%s,%s,current_timestamp,current_timestamp,%s,%s,%s)', (pensioner.id,upload.id,payment_code,data_row[1],data_row[2],self.env.user.id,self.env.user.id,'f'))
                                    if pensioner.work_email:
                                        message = "Dear Sir,\nYour pension with details as shown below has been approved for payment:\n\nNARRATION: " + data_row[1] + "\nAMOUNT: " + 'NGN{:,.2f}'.format(data_row[2]) + "\n\nPlease confirm payment with PAYMENT CODE: " + payment_code + ".\n\nThank you.\n"
                                        receivers = [pensioner.work_email] #Comma separated email addresses
                                        msg = MIMEMultipart()
                                        msg['Subject'] = 'I am Alive Confirmation' 
                                        msg['From'] = sender
                                        msg['To'] = ', '.join(receivers)
                                        msg.attach(MIMEText(message))
                                                                                
                                        smtp_obj.sendmail(sender, receivers, msg.as_string())
                                        _logger.info("Email successfully sent to: " + msg['To'])         
                                
                if len(exception_list) > 0:
                    with open('/tmp/payment_upload_exceptions.csv', 'w') as csvfile:
                        fieldnames = ['pin', 'narration', 'amount','error']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(exception_list)
                        csvfile.close()

                self.env.cr.execute("update imalive_pension_payment set state='approved' where id=" + str(upload.id))

                message = "Hello Sir,\nUpload of payment instruction file has completed.\n\nThank you.\n"
                message_exception = "\nPS: There were " + str(len(exception_list)) + " exceptions."
                receivers = [upload.notify_emails] #Comma separated email addresses
                msg = MIMEMultipart()
                msg['Subject'] = 'Payment Instructions Approved' 
                msg['From'] = sender
                msg['To'] = ', '.join(receivers)
                                 
                part = False
                if len(exception_list) > 0:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(open("/tmp/payment_upload_exceptions.csv", "rb").read())
                    Encoders.encode_base64(part)                            
                    part.add_header('Content-Disposition', 'attachment; filename="nonstd_earnded_upload_exceptions.csv"')
                message = message + message_exception
                msg.attach(MIMEText(message))
                            
                if part:
                    msg.attach(part)
                                                        
                smtp_obj.sendmail(sender, receivers, msg.as_string())         
                _logger.info("Email successfully sent to: " + msg['To'])                        
            else:
                return False

        return True
   
class PensionerEnrollment(models.Model):
    '''
    Pensioner Enrollment Request
    '''
    _name = "imalive.pension.enrollment"
    _description = 'Pensioner Enrollment Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    pensioner_id = fields.Many2one('hr.employee', 'Pensioner', required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled'),
        ], 'State', readonly=True)
    date = fields.Date('Effective Date', required=True, states={'draft': [('readonly', False)]})
    sinid = fields.Char(related='pensioner_id.sinid', store=False)
    mobile_phone = fields.Char(related='pensioner_id.mobile_phone', store=False)
    gender = fields.Selection(related='pensioner_id.gender', store=False)
    identification_id = fields.Char(related='pensioner_id.identification_id', store=False)
    name_related = fields.Char(related='pensioner_id.name_related', store=False)
    hire_date = fields.Date(related='pensioner_id.hire_date', store=False)
    retirement_date = fields.Date(related='pensioner_id.retirement_date', store=False)
    bank_account_no = fields.Char(related='pensioner_id.bank_account_no', store=False)
    title_id = fields.Many2one(related='pensioner_id.title_id', store=False)
    bank_id = fields.Many2one(related='pensioner_id.bank_id', store=False)
 
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
        'date': date.today(),
    }
       
    _track = {
        'state': {
            'imalive_pension_enrollment.mt_alert_enrollment_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'imalive_pension_enrollment.mt_alert_enrollment_pending':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'imalive_pension_enrollment.mt_alert_enrollment_done':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approved',
        },
    }

    @api.multi
    def _check_state(self, pensioner_id, effective_date, context=None):
        _logger.info("_check_state - %d", pensioner_id)
                
        return True
    
    @api.model
    def _needaction_domain_get(self, context=None):
        users_obj = self.pool.get('res.users')
        _logger.info("_needaction_domain_get - %s", users_obj)

        if self.env.user.has_group('im_alive_pension.group_pension_administrator'):
            _logger.info("_needaction_domain_get - is HR Manager")
            domain = [('state', '=', 'confirm')]
            return domain

        return False
    
    @api.multi
    def unlink(self, context=None):
        for item_obj in self.browse(self.ids):
            if item_obj.state not in ['draft']:
                raise exceptions.except_orm(
                    _('Unable to Delete Payment Upload action!'),
                    _('Payment Upload action has been initiated. Either cancel the action or create another to undo it.')
                )

        return super(PensionerEnrollment, self).unlink()

    @api.multi
    def effective_date_in_future(self, context=None):

        today = datetime.now().date()
        for o in self.browse(self.ids):
            effective_date = datetime.strptime(
                o.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False

        return True

    @api.multi
    def enrollment_state_confirm(self, context=None):
        _logger.info("before state_confirm - %d", self.env.user.id)
        for o in self.browse(self.ids):
            self._check_state(o.id, o.date, context=context)
            self.write({'id':o.id, 'state': 'confirm'})
        _logger.info("after state_confirm - %d", self.env.user.id)
        return True

    @api.multi
    def enrollment_state_done(self, enrol_ids, context=None):
        _logger.info("Calling enrollment_state_done...")
        #pensioner_obj = self.env['hr.employee']
        today = datetime.now().date()

        smtp_obj = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
        smtp_obj.ehlo()
        #smtp_obj.starttls()
        #smtp_obj.ehlo()
        smtp_obj.login(user="osun.payroll@gmail.com", password="p@55w0rd1939")
        sender = 'osun.payroll@gmail.com'
        #self.env.cr.execute("update hr_employee set active='t' where id in (" + str(enrol_ids).replace('[', '').replace(']', '') + ")")
        for o in self.browse(enrol_ids):
            if datetime.strptime(
                o.date, DEFAULT_SERVER_DATE_FORMAT
            ).date() <= today and o.state == 'pending':
                self._check_state(o.id, o.date, context=context)
                _logger.info("enrollment_state_done - pensioner_id: %s", o.pensioner_id.id)
                self.env.cr.execute("update hr_employee set active='t' where id=(" + str(o.pensioner_id.id) + ")")
                #emp_dict = {'id': o.pensioner_id.id, 'active': True}
                _logger.info("enrollment_state_done...employee activated")
                #pensioner_obj.write(emp_dict)
                #self.write({'id': o.id, 'state': 'approved'})
                self.env.cr.execute("update imalive_pension_enrollment set state='approved' where id=(" + str(o.id) + ")")
                if o.pensioner_id.work_email:
                    message = "Dear Sir,\nYour enrollment details as shown below has been approved:\n\n" + "NAME: " + o.pensioner_id.name_related + "\nPENSION NO: " + o.pensioner_id.sinid + "\nMOBILE NO: " + o.pensioner_id.mobile_phone + "\nBANK: " + o.pensioner_id.bank_id.name + "\nBANK ACCT: " + o.pensioner_id.bank_account_no + ".\n\nThank you.\n"
                    receivers = [o.pensioner_id.work_email] #Comma separated email addresses
                    msg = MIMEMultipart()
                    msg['Subject'] = 'Enrollment Approved' 
                    msg['From'] = sender
                    msg['To'] = ', '.join(receivers)
                    msg.attach(MIMEText(message))
                                                            
                    smtp_obj.sendmail(sender, receivers, msg.as_string())
                    _logger.info("Email successfully sent to: " + msg['To'])         
                
                _logger.info("enrollment_state_done...approved")
            else:
                return False
        return True

    @api.multi
    def try_pending_enrollment_actions(self, context=None):
        """Completes pending enrollment actions. Called from
        the scheduler."""

        _logger.info("Running try_pending_enrollment_actions cron-job...")
        
        enrol_obj = self.env['imalive.pension.enrollment']
        today = datetime.now().date()
        enrol_ids = enrol_obj.search([
            ('state', '=', 'pending'),
            ('date', '<=', today.strftime(
                DEFAULT_SERVER_DATE_FORMAT))])

        self.enrollment_state_done(enrol_ids.ids)

        return True
    
class Disability(models.Model):
    '''
    Disability
    '''
    _name = "imalive.pension.disability"
    _description = 'Disability'
    
    name = fields.Char(string='Disability', required=True)
    active = fields.Boolean('Active', help='Active Status', required=True)

    
class ChamsSwitchConfig(models.Model):
    _name = "imalive.pension.chamsswitch.config"
    _description = "Chams Switch Configuration"

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', help='Active Status', required=True)
    testing = fields.Boolean('Testing', help='Testing', required=True)
    test_content = fields.Text('Test Content', required=True)
    url = fields.Char('Chams Switch URL', required=True)
    http_meth = fields.Selection([
        ('post', 'POST'), 
        ('get', 'GET'), 
        ('put', 'PUT'), 
        ('patch', 'PATCH'), 
        ('delete', 'DELETE')], string='HTTP Method')
    user = fields.Char('Username', required=False)
    passwd = fields.Char('Password', required=False)
    
    _defaults = {
        'name': 'Test Configuration',
        'active': True,
        'testing': True,
        'url': 'http://e2e6dbbd.ngrok.io/ChamsPay/rest/chams/upload',
        'http_meth': 'post',
        'test_content': '{"terminalId":"0000001","totalAmount":10000,"totalCount":3,"scheduleIdentifier":"jfduuf020000","uploadList":[{"staffId":"1","name":"James Doe","emailAddress":"doe@gmail.com","mobile":"080","amount":1000,"bankCode":"011","accountNumber":"1122334455","paymentId":"0001"},{"staffId":"2","name":"Jane Doe","emailAddress":"jane.doe@gmail.com","mobile":"080","amount":2000,"bankCode":"014","accountNumber":"5544332211","paymentId":"0002"},{"staffId":"3","name":"Shane Doe","emailAddress":"shane.doe@gmail.com","mobile":"080","amount":3000,"bankCode":"032","accountNumber":"5544332211","paymentId":"0003"}]}'
    } 
    
class ChamsSwitchBatch(models.Model):
    '''
    Chams Switch Batch Payment
    '''
    _name = "imalive.pension.chamsswitch.batch"
    _description = 'Chams Switch Batch Payment'
    
    name = fields.Char(related='payment_inst_id.name', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], 'State', readonly=True)
    payment_inst_id = fields.Many2one('imalive.pension.payment', 'Payment Batch', required=True, domain="[('state','=','closed')]")
    payment_ids = fields.One2many('imalive.pension.chamsswitch.payment','batch_id','Payment Lines')
    
    _defaults = {
        'state': 'draft',
    }
     
    @api.multi
    def cancel(self):
        _logger.info("cancel - %s", 'cancel')
        self.write({'state':'cancel'})
     
    @api.multi
    def confirm(self):
        _logger.info("confirm - %s", 'confirm')
        self.write({'state':'confirm'})
            
    @api.multi
    def approve(self):
        _logger.info("approve - %s", 'approve')
        self.write({'state':'approved'})
        
    @api.multi
    def update_payment_status(self, schedule_id, staff_id, status):
        _logger.info("Calling update_payment_status...%s, %s", schedule_id, staff_id, status)
        
        if schedule_id and staff_id and status:
            payment_instance = self.env['imalive.pension.chamsswitch.payment'].search([('employee_id', '=', staff_id),('batch_id', '=', schedule_id)])
            if payment_instance:
                payment_instance.write({'state': status})
            else:
                return "No payment instance with payment_id '" + staff_id + "' found."
        else:
            return "Request has no payment_id and/or status parameters."
        
        return True
        
    @api.multi
    def update_payment_statuses(self, schedule_id, staff_ids, statuses):
        _logger.info("Calling update_payment_status...%s, %s, %s", schedule_id, staff_ids, statuses)
        
        if schedule_id and staff_ids and statuses:
            if len(staff_ids) != len(statuses):
                return "Number of payment_ids must match number of statuses"
            
            for idx in range(len(staff_ids)):
                payment_instance = self.env['imalive.pension.chamsswitch.payment'].search([('id', '=', staff_ids[idx],('batch_id', '=', schedule_id))])
                if payment_instance:
                    payment_instance.write({'state': statuses[idx]})
                else:
                    return "No payment instance with payment_id '" + staff_ids[idx] + "' found."
        else:
            return "Request has no payment_id and/or status parameters."
        
        return True
    
    @api.model
    def process_payment(self, context=None):
        _logger.info("Calling process_payment...state = %s", self.state)
        if self.state == 'closed':
            self.state = 'paid'
            serial_no = 1
            
            payment_items = self.payment_inst_id.payment_item_ids.filtered(lambda r: r.active == True)
            if payment_items:
                for item in payment_items:
                    self.payment_ids.update({'serial_no':serial_no,'batch_id':self.id,'employee_id':item.pensioner_id.id,'amount':item.amount})
                    serial_no += 1
    
    @api.model   
    def send_batch(self, context=None):
        _logger.info("Calling send_batch...")
        
        config_instance = self.env['imalive.pension.chamsswitch.config'].search([('active', '=', True)])
        active_config = config_instance[0]
        auth = None
        if active_config.user and active_config.passwd:
            auth = (active_config.user, active_config.passwd)
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        
        req = active_config.test_content
        if not active_config.testing and self.payment_ids:
            #TODO Generate JSON request
            req = {
                'terminalId':'0000001',
                'totalAmount':0,
                'totalCount':len(self.payment_ids),
                'scheduleIdentifier':'OSSG' + str(self.id).zfill(6),
                'uploadList':[]
            }
            
            totalAmount = 0
            uploadList = []
            for payment_id in self.payment_ids:
                totalAmount += payment_id.amount
                uploadList.append({
                    'staffId':payment_id.employee_id.id,
                    'name':payment_id.employee_id.name_related,
                    'emailAddress':payment_id.employee_id.work_email,
                    'mobile':payment_id.employee_id.mobile_phone,
                    'accountNumber':payment_id.employee_id.bank_account_no,
                    'bankCode':payment_id.employee_id.bank_id.code,
                    'amount':payment_id.amount
                })
            
            req.update({'totalAmount':totalAmount,'uploadList':uploadList})
                
        result = getattr(requests, active_config.test_meth)(active_config.url, req, auth=auth, headers=headers)
        _logger.info("send_batch result=%s", result.text)
            
        return True
    
class ChamsSwitchPayment(models.Model):
    '''
    Chams Switch Payment
    '''
    _name = "imalive.pension.chamsswitch.payment"
    _description = 'Chams Switch Payment'
    
    batch_id = fields.Many2one('imalive.pension.chamsswitch.batch', 'Payment Batch', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    serial_no = fields.Char('Serial Number', help='Serial Number', required=True)
    amount = fields.Float('Amount', help='Amount', required=True)
    state = fields.Selection([
        ('00', 'Successful'),
        ('01', 'DUPLICATE UPLOAD'),
        ('02', 'MANDATORY FIELD NOT SET'),
        ('03', 'UNKNOWN TERMINAL ID'),
        ('05', 'FORMAT ERROR'),
        ('06', 'IN PROGRESS'),
        ('99', 'SYSTEM ERROR'),
        ('09', 'REJECTED BY APPROVER'),
        ('10', 'INVALID NUBAN NUMBER'),
        ('11', 'PAYMENT DISHONOURED BY BANK'),
        ('12', 'PROCESSING COMPLETED WITH ERROR'),
        ('14', 'RECORD NOT FOUND'),
        ('15', 'PAYMENT FAILED'),
        ('16', 'REQUEST ACCEPTED'),
        ('17', 'PAYMENT SCHEDULE NOT FOUND'),
        ('18', 'INVALID SCHEDULE ID'),
        ('19', 'BENEFICIARY BANK NOT AVAILABLE'),
        ('20', 'DO NOT HONOR'),
        ('21', 'DORMANT ACCOUNT'),
        ('22', 'INVALID BANK CODE'),
        ('23', 'INVALID BANK ACCOUNT'),
        ('24', 'CANNOT VERIFY ACCOUNT'),
    ], 'State', required=False, readonly=True)
