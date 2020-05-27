# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Systempay plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import base64
from datetime import datetime
from hashlib import sha1, sha256
import hmac
import logging
import math
from os import path

from pkg_resources import parse_version

from odoo import models, api, release, fields, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools import convert_xml_import
from odoo.tools import float_round
from odoo.tools.float_utils import float_compare

from ..controllers.main import SystempayController
from ..helpers import constants, tools
from .card import SystempayCard
from .language import SystempayLanguage


try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

_logger = logging.getLogger(__name__)

class AcquirerSystempay(models.Model):
    _inherit = 'payment.acquirer'

    def _get_notify_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return urlparse.urljoin(base_url, SystempayController._notify_url)

    def _get_languages(self):
        languages = constants.SYSTEMPAY_LANGUAGES
        return [(c, _(l)) for c, l in languages.items()]

    @api.depends('provider')
    def _compute_multi_warning(self):
        for acquirer in self:
            acquirer.systempay_multi_warning = (constants.SYSTEMPAY_PLUGIN_FEATURES.get('restrictmulti') == True) if (acquirer.provider == 'systempaymulti') else False

    sign_algo_help = _('Algorithm used to compute the payment form signature. Selected algorithm must be the same as one configured in the Systempay Back Office.')

    if constants.SYSTEMPAY_PLUGIN_FEATURES.get('shatwo') == False:
        sign_algo_help += _('The HMAC-SHA-256 algorithm should not be activated if it is not yet available in the Systempay Back Office, the feature will be available soon.')

    providers = [('systempay', _('Systempay - Standard payment'))]

    if constants.SYSTEMPAY_PLUGIN_FEATURES.get('multi') == True:
        providers.append(('systempaymulti', _('Systempay - Payment in installments')))

    provider = fields.Selection(selection_add=providers)

    systempay_site_id = fields.Char(string=_('Shop ID'), help=_('The identifier provided by Systempay.'), default=constants.SYSTEMPAY_PARAMS.get('SITE_ID'))
    systempay_key_test = fields.Char(string=_('Key in test mode'), help=_('Key provided by Systempay for test mode (available in Systempay Back Office).'), default=constants.SYSTEMPAY_PARAMS.get('KEY_TEST'), readonly=constants.SYSTEMPAY_PLUGIN_FEATURES.get('qualif'))
    systempay_key_prod = fields.Char(string=_('Key in production mode'), help=_('Key provided by Systempay (available in Systempay Back Office after enabling production mode).'), default=constants.SYSTEMPAY_PARAMS.get('KEY_PROD'))
    systempay_sign_algo = fields.Selection(string=_('Signature algorithm'), help=sign_algo_help, selection=[('SHA-1', 'SHA-1'), ('SHA-256', 'HMAC-SHA-256')], default=constants.SYSTEMPAY_PARAMS.get('SIGN_ALGO'))
    systempay_notify_url = fields.Char(string=_('Instant Payment Notification URL'), help=_('URL to copy into your Systempay Back Office > Settings > Notification rules.'), default=_get_notify_url, readonly=True)
    systempay_gateway_url = fields.Char(string=_('Payment page URL'), help=_('Link to the payment page.'), default=constants.SYSTEMPAY_PARAMS.get('GATEWAY_URL'))
    systempay_language = fields.Selection(string=_('Default language'), help=_('Default language on the payment page.'), default=constants.SYSTEMPAY_PARAMS.get('LANGUAGE'), selection=_get_languages)
    systempay_available_languages = fields.Many2many('systempay.language', string=_('Available languages'), column1='code', column2='label', help=_('Languages available on the payment page. If you do not select any, all the supported languages will be available.'))
    systempay_capture_delay = fields.Char(string=_('Capture delay'), help=_('The number of days before the bank capture (adjustable in your Systempay Back Office).'))
    systempay_validation_mode = fields.Selection(string=_('Validation mode'), help=_('If manual is selected, you will have to confirm payments manually in your Systempay Back Office.'), selection=[('-1', _('Systempay Back Office Configuration')), ('0', _('Automatic')), ('1', _('Manual'))])
    systempay_payment_cards = fields.Many2many('systempay.card', string=_('Card types'), column1='code', column2='label', help=_('The card type(s) that can be used for the payment. Select none to use gateway configuration.'))
    systempay_threeds_min_amount = fields.Char(string=_('Disable 3DS'), help=_('Amount below which 3DS will be disabled. Needs subscription to selective 3DS option. For more information, refer to the module documentation.'))
    systempay_redirect_enabled = fields.Selection(string=_('Automatic redirection'), help=_('If enabled, the buyer is automatically redirected to your site at the end of the payment.'), selection=[('0', _('Disabled')), ('1', _('Enabled'))])
    systempay_redirect_success_timeout = fields.Char(string=_('Redirection timeout on success'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a successful payment.'))
    systempay_redirect_success_message = fields.Char(string=_('Redirection message on success'), help=_('Message displayed on the payment page prior to redirection after a successful payment.'), default=_('Redirection to shop in a few seconds...'))
    systempay_redirect_error_timeout = fields.Char(string=_('Redirection timeout on failure'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a declined payment.'))
    systempay_redirect_error_message = fields.Char(string=_('Redirection message on failure'), help=_('Message displayed on the payment page prior to redirection after a declined payment.'), default=_('Redirection to shop in a few seconds...'))
    systempay_return_mode = fields.Selection(string=_('Return mode'), help=_('Method that will be used for transmitting the payment result from the payment page to your shop.'), selection=[('GET', 'GET'), ('POST', 'POST')])
    systempay_multi_warning = fields.Boolean(compute='_compute_multi_warning')

    systempay_multi_count = fields.Char(string=_('Count'), help=_('Total number of payments.'))
    systempay_multi_period = fields.Char(string=_('Period'), help=_('Delay (in days) between payments.'))
    systempay_multi_first = fields.Char(string=_('1st payment'), help=_('Amount of first payment, in percentage of total amount. If empty, all payments will have the same amount.'))

    # Check if it's Odoo 10.
    systempay_odoo10 = True if parse_version(release.version) < parse_version('11') else False

    # Compatibility betwen Odoo 13 and previous versions.
    systempay_odoo13 = True if parse_version(release.version) >= parse_version('13') else False

    if systempay_odoo13:
        image = fields.Char()
        environment = fields.Char()
    else:
        image_128 = fields.Char()
        state = fields.Char()

    @api.model
    def multi_add(self, filename):
        file = path.join(path.dirname(path.dirname(path.abspath(__file__)))) + filename

        if (constants.SYSTEMPAY_PLUGIN_FEATURES.get('multi') == True):
            convert_xml_import(self._cr, 'payment_systempay', file)

        return None

    def _get_ctx_mode(self):
        ctx_key = self.state if self.systempay_odoo13 else self.environment
        ctx_value = 'TEST' if ctx_key == 'test' else 'PRODUCTION'

        return ctx_value

    def _systempay_generate_sign(self, acquirer, values):
        key = self.systempay_key_prod if self._get_ctx_mode() == 'PRODUCTION' else self.systempay_key_test

        sign = ''
        for k in sorted(values.keys()):
            if k.startswith('vads_'):
                sign += values[k] + '+'

        sign += key

        if self.systempay_sign_algo == 'SHA-1':
            shasign = sha1(sign.encode('utf-8')).hexdigest()
        else:
            shasign = base64.b64encode(hmac.new(key.encode('utf-8'), sign.encode('utf-8'), sha256).digest()).decode('utf-8')

        return shasign

    def _get_payment_config(self, amount):
        if self.provider == 'systempaymulti':
            if (self.systempay_multi_first):
                first = int(float(self.systempay_multi_first) / 100 * int(amount))
            else:
                first = int(float(amount) / float(self.systempay_multi_count))

            payment_config = u'MULTI:first=' + str(first) + u';count=' + self.systempay_multi_count + u';period=' + self.systempay_multi_period
        else:
            payment_config = u'SINGLE'

        return payment_config

    def systempay_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # trans_id is the number of 1/10 seconds from midnight.
        now = datetime.now()
        midnight = now.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        delta = int((now - midnight).total_seconds() * 10)
        trans_id = str(delta).rjust(6, '0')

        threeds_mpi = u''
        if self.systempay_threeds_min_amount and float(self.systempay_threeds_min_amount) > values['amount']:
            threeds_mpi = u'2'

        # Check currency.
        currency_num = tools.find_currency(values['currency'].name)
        if currency_num is None:
            _logger.error('The plugin cannot find a numeric code for the current shop currency {}.'.format(values['currency'].name))
            raise ValidationError(_('The shop currency {} is not supported.').format(values['currency'].name))

        # Amount in cents.
        k = int(values['currency'].decimal_places)
        amount = int(float_round(float_round(values['amount'], k) * (10 ** k), 0))

        # List of available languages.
        available_languages = ''
        for value in self.systempay_available_languages:
            available_languages += value.code + ';'

        # List of available payment cards.
        payment_cards = ''
        for value in self.systempay_payment_cards:
            payment_cards += value.code + ';'

        #Validation mode
        validation_mode = self.systempay_validation_mode if self.systempay_validation_mode != '-1' else ''

        # Enable redirection?
        self.systempay_redirect = True if str(self.systempay_redirect_enabled) == '1' else False

        tx_values = dict() # Values to sign in unicode.
        tx_values.update({
            'vads_site_id': self.systempay_site_id,
            'vads_amount': str(amount),
            'vads_currency': currency_num,
            'vads_trans_date': str(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            'vads_trans_id': str(trans_id),
            'vads_ctx_mode': str(self._get_ctx_mode()),
            'vads_page_action': u'PAYMENT',
            'vads_action_mode': u'INTERACTIVE',
            'vads_payment_config': self._get_payment_config(amount),
            'vads_version': constants.SYSTEMPAY_PARAMS.get('GATEWAY_VERSION'),
            'vads_url_return': urlparse.urljoin(base_url, SystempayController._return_url),
            'vads_order_id': str(values.get('reference')),
            'vads_contrib': constants.SYSTEMPAY_PARAMS.get('CMS_IDENTIFIER') + u'_' + constants.SYSTEMPAY_PARAMS.get('PLUGIN_VERSION') + u'/' + release.version,

            'vads_language': self.systempay_language or '',
            'vads_available_languages': available_languages,
            'vads_capture_delay': self.systempay_capture_delay or '',
            'vads_validation_mode': validation_mode,
            'vads_payment_cards': payment_cards,
            'vads_return_mode': str(self.systempay_return_mode),
            'vads_threeds_mpi': threeds_mpi,

            # Customer info.
            'vads_cust_id': str(values.get('billing_partner_id')) or '',
            'vads_cust_first_name': values.get('billing_partner_first_name') and values.get('billing_partner_first_name')[0:62] or '',
            'vads_cust_last_name': values.get('billing_partner_last_name') and values.get('billing_partner_last_name')[0:62] or '',
            'vads_cust_address': values.get('billing_partner_address') and values.get('billing_partner_address')[0:254] or '',
            'vads_cust_zip': values.get('billing_partner_zip') and values.get('billing_partner_zip')[0:62] or '',
            'vads_cust_city': values.get('billing_partner_city') and values.get('billing_partner_city')[0:62] or '',
            'vads_cust_state': values.get('billing_partner_state').code and values.get('billing_partner_state').code[0:62] or '',
            'vads_cust_country': values.get('billing_partner_country').code and values.get('billing_partner_country').code.upper() or '',
            'vads_cust_email': values.get('billing_partner_email') and values.get('billing_partner_email')[0:126] or '',
            'vads_cust_phone': values.get('billing_partner_phone') and values.get('billing_partner_phone')[0:31] or '',

            # Shipping info.
            'vads_ship_to_first_name': values.get('partner_first_name') and values.get('partner_first_name')[0:62] or '',
            'vads_ship_to_last_name': values.get('partner_last_name') and values.get('partner_last_name')[0:62] or '',
            'vads_ship_to_street': values.get('partner_address') and values.get('partner_address')[0:254] or '',
            'vads_ship_to_zip': values.get('partner_zip') and values.get('partner_zip')[0:62] or '',
            'vads_ship_to_city': values.get('partner_city') and values.get('partner_city')[0:62] or '',
            'vads_ship_to_state': values.get('partner_state').code and values.get('partner_state').code[0:62] or '',
            'vads_ship_to_country': values.get('partner_country').code and values.get('partner_country').code.upper() or '',
            'vads_ship_to_phone_num': values.get('partner_phone') and values.get('partner_phone')[0:31] or '',
        })

        if self.systempay_redirect:
            tx_values.update({
                'vads_redirect_success_timeout': self.systempay_redirect_success_timeout or '',
                'vads_redirect_success_message': self.systempay_redirect_success_message or '',
                'vads_redirect_error_timeout': self.systempay_redirect_error_timeout or '',
                'vads_redirect_error_message': self.systempay_redirect_error_message or ''
            })

        systempay_tx_values = dict() # Values encoded in UTF-8.

        for key in tx_values.keys():
            if tx_values[key] == ' ':
                tx_values[key] = ''

            systempay_tx_values[key] = tx_values[key].encode('utf-8')

        systempay_tx_values['systempay_signature'] = self._systempay_generate_sign(self, tx_values)
        return systempay_tx_values

    def systempaymulti_form_generate_values(self, values):
        return self.systempay_form_generate_values(values)

    def systempay_get_form_action_url(self):
        return self.systempay_gateway_url

    def systempaymulti_get_form_action_url(self):
        return self.systempay_gateway_url

class TransactionSystempay(models.Model):
    _inherit = 'payment.transaction'

    systempay_trans_status = fields.Char(_('Transaction status'))
    systempay_card_brand = fields.Char(_('Means of payment'))
    systempay_card_number = fields.Char(_('Card number'))
    systempay_expiration_date = fields.Char(_('Expiration date'))
    systempay_auth_result = fields.Char(_('Authorization result'))
    systempay_raw_data = fields.Text(string=_('Transaction log'), readonly=True)

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _systempay_form_get_tx_from_data(self, data):
        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')

        if not reference or not shasign or not status:
            error_msg = 'Systempay : received bad data {}'.format(data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Systempay: received data for reference {}'.format(reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # Verify shasign.
        shasign_check = tx.acquirer_id._systempay_generate_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'Systempay: invalid shasign, received {}, computed {}, for data {}'.format(shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _systempay_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # Check what is bought.
        amount = float(int(data.get('vads_amount', 0)) / math.pow(10, int(self.currency_id.decimal_places)))

        if float_compare(amount, self.amount, int(self.currency_id.decimal_places)) != 0:
            invalid_parameters.append(('amount', amount, '{:.2f}'.format(self.amount)))

        currency_code = tools.find_currency(self.currency_id.name)
        if (currency_code is None) or (int(data.get('vads_currency')) != int(currency_code)):
            invalid_parameters.append(('currency', data.get('vads_currency'), currency_code))

        return invalid_parameters

    def _systempay_form_validate(self, data):
        systempay_statuses = {
            'success': ['AUTHORISED', 'CAPTURED', 'ACCEPTED'],
            'pending': ['AUTHORISED_TO_VALIDATE', 'WAITING_AUTHORISATION', 'WAITING_AUTHORISATION_TO_VALIDATE', 'INITIAL', 'UNDER_VERIFICATION', 'WAITING_FOR_PAYMENT', 'PRE_AUTHORISED'],
            'cancel': ['ABANDONED']
        }

        html_3ds = _('3DS authentication: ')
        if data.get('vads_threeds_status') == 'Y':
            html_3ds += _('YES')
            html_3ds += '<br />' + _('3DS certificate: ') + data.get('vads_threeds_cavv')
        else:
            html_3ds += _('NO')

        expiry = ''
        if data.get('vads_expiry_month') and data.get('vads_expiry_year'):
            expiry = data.get('vads_expiry_month').zfill(2) + '/' + data.get('vads_expiry_year')

        values = {
            'acquirer_reference': data.get('vads_trans_uuid'),
            'systempay_raw_data': '{}'.format(data),
            'html_3ds': html_3ds,
            'systempay_trans_status': data.get('vads_trans_status'),
            'systempay_card_brand': data.get('vads_card_brand'),
            'systempay_card_number': data.get('vads_card_number'),
            'systempay_expiration_date': expiry,
        }

        # Set validation date.
        key = 'date' if hasattr(self, 'date')  else 'date_validate'
        values[key] = fields.Datetime.now()

        status = data.get('vads_trans_status')
        if status in systempay_statuses['success']:
            values.update({
                'state': 'done',
            })

            self.write(values)

            return True
        elif status in systempay_statuses['pending']:
            values.update({
                'state': 'pending',
            })

            self.write(values)

            return True
        elif status in systempay_statuses['cancel']:
            self.write({
                'state_message': 'Payment for transaction #%s is cancelled (%s).' % (self.reference, data.get('vads_result')),
                'state': 'cancel',
            })

            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = _('See the transaction details for more information ({}).').format(auth_result)

            error_msg = 'Systempay payment error, transaction status: {}, authorization result: {}.'.format(status, auth_result)
            _logger.info(error_msg)

            values.update({
                'state_message': 'Payment for transaction #%s is refused (%s).' % (self.reference, data.get('vads_result')),
                'state': 'error',
                'systempay_auth_result': auth_message,
            })

            self.write(values)

            return False
