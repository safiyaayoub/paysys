# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Systempay plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import _

# WARN: Do not modify code format here. This is managed by build files. 
SYSTEMPAY_PLUGIN_FEATURES = {
    'multi': True,
    'restrictmulti': False,
    'qualif': False,
    'shatwo': True,
}

SYSTEMPAY_PARAMS = {
    'GATEWAY_CODE': 'Systempay',
    'GATEWAY_NAME': 'Systempay',
    'BACKOFFICE_NAME': 'Systempay',
    'SUPPORT_EMAIL': 'supportvad@lyra-network.com',
    'GATEWAY_URL': 'https://paiement.systempay.fr/vads-payment/',
    'SITE_ID': '12345678',
    'KEY_TEST': '1111111111111111',
    'KEY_PROD': '2222222222222222',
    'CTX_MODE': 'TEST',
    'SIGN_ALGO': 'SHA-256',
    'LANGUAGE': 'fr',

    'GATEWAY_VERSION': 'V2',
    'PLUGIN_VERSION': '1.2.0',
    'CMS_IDENTIFIER': 'Odoo_10-13',
}

SYSTEMPAY_LANGUAGES = {
    'cn': 'Chinese',
    'de': 'German',
    'es': 'Spanish',
    'en': 'English',
    'fr': 'French',
    'it': 'Italian',
    'jp': 'Japanese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'sv': 'Swedish',
    'tr': 'Turkish',
}

SYSTEMPAY_CARDS = {
    'CB': u'CB',
    'E-CARTEBLEUE': u'e-Carte Bleue',
    'MAESTRO': u'Maestro',
    'MASTERCARD': u'MasterCard',
    'VISA': u'Visa',
    'VISA_ELECTRON': u'Visa Electron',
    'VPAY': u'V PAY',
    'AMEX': u'American Express',
    'AURORE-MULTI': u'Cpay Aurore',
    'BANCONTACT': u'Bancontact Mistercash',
    'CA_DO_CARTE': u'CA DO Carte',
    'COFINOGA': u'Carte Cofinoga Be Smart',
    'CONECS': u'Titre-Restaurant Dématérialisé Conecs',
    'APETIZ': u'Titre-Restaurant Dématérialisé Apetiz',
    'CHQ_DEJ': u'Titre-Restaurant Dématérialisé Chèque Déjeuner',
    'SODEXO': u'Titre-Restaurant Dématérialisé Sodexo',
    'EDENRED': u'Ticket Restaurant',
    'JOUECLUB_CDX': u'Carte Cadeau Joué Club',
    'JOUECLUB_CDX_SB': u'Carte Cadeau Joué Club (sandbox)',
    'DINERS': u'Carte Diners Club',
    'DISCOVER': u'Carte Discover',
    'ECCARD': u'Euro-Cheque card',
    'EPNF_3X': u'Paiment Choozeo 3X',
    'EPNF_4X': u'Paiment Choozeo 4X',
    'GOOGLEPAY': u'Google Pay',
    'GIROPAY': u'Giropay',
    'IDEAL': u'iDEAL',
    'ILLICADO': u'Carte Cadeau Illicado',
    'ILLICADO_SB': u'Carte Cadeau Illicado - Sandbox',
    'JCB': u'JCB',
    'KLARNA': u'Klarna Internet Banking',
    'MASTERPASS': u'MasterPass',
    'ONEY': u'FacilyPay Oney',
    'ONEY_SANDBOX': u'FacilyPay Oney - Sandbox',
    'ONEY_3X_4X': u'Paiement en 3 ou 4 fois Oney',
    'PAYLIB': u'Wallet Paylib',
    'PAYPAL': u'PayPal',
    'PAYPAL_SB': u'PayPal - Sandbox',
    'POSTFINANCE': u'PostFinance',
    'POSTFINANCE_EFIN': u'PostFinance E-finance',
    'SDD': u'Prélèvement SEPA Direct Debit',
    'SOFICARTE': u'Soficarte',
    'SOFORT_BANKING': u'Sofort',
    'ONEY_ENSEIGNE': u'Cartes enseignes Oney',
}

SYSTEMPAY_CURRENCIES = [
    ['AUD', '036', 2],
    ['KHR', '116', 0],
    ['CAD', '124', 2],
    ['CNY', '156', 1],
    ['HRK', '191', 2],
    ['CZK', '203', 2],
    ['DKK', '208', 2],
    ['HKD', '344', 2],
    ['HUF', '348', 2],
    ['INR', '356', 2],
    ['IDR', '360', 2],
    ['JPY', '392', 0],
    ['KRW', '410', 0],
    ['MYR', '458', 2],
    ['MXN', '484', 2],
    ['NZD', '554', 2],
    ['NOK', '578', 2],
    ['PHP', '608', 2],
    ['RUB', '643', 2],
    ['SGD', '702', 2],
    ['ZAR', '710', 2],
    ['SEK', '752', 2],
    ['CHF', '756', 2],
    ['THB', '764', 2],
    ['GBP', '826', 2],
    ['USD', '840', 2],
    ['TWD', '901', 2],
    ['RON', '946', 2],
    ['TRY', '949', 2],
    ['XPF', '953', 0],
    ['BGN', '975', 2],
    ['EUR', '978', 2],
    ['PLN', '985', 2],
    ['BRL', '986', 2],
]
