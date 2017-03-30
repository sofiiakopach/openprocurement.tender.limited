# -*- coding: utf-8 -*-
from datetime import timedelta
from openprocurement.api.utils import (
    get_now,
    json_view,
    context_unpack,
    APIResource,
    error_handler
)

from openprocurement.tender.core.utils import (
    apply_patch, save_tender, optendersresource
)

from openprocurement.tender.belowthreshold.validation import (
    validate_patch_award_data, validate_award_data,
)

from openprocurement.tender.core.utils import calculate_business_date  # TODO check imports when openua refactoring is finished

from openprocurement.tender.openua.models import calculate_normalized_date

from openprocurement.tender.limited.validation import (
    validate_create_new_award,
    validate_lot_cancellation,
    validate_create_new_award_with_lots,
    validate_award_operation_not_in_active_status
)


@optendersresource(name='reporting:Tender Awards',
                   collection_path='/tenders/{tender_id}/awards',
                   path='/tenders/{tender_id}/awards/{award_id}',
                   description="Tender awards",
                   procurementMethodType='reporting',
                   )
class TenderAwardResource(APIResource):

    @json_view(permission='view_tender')
    def collection_get(self):
        """Tender Awards List

        Get Awards List
        ---------------

        Example request to get awards list:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": [
                    {
                        "status": "active",
                        "suppliers": [
                            {
                                "id": {
                                    "name": "Державне управління справами",
                                    "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                    "uid": "00037256",
                                    "uri": "http://www.dus.gov.ua/"
                                },
                                "address": {
                                    "countryName": "Україна",
                                    "postalCode": "01220",
                                    "region": "м. Київ",
                                    "locality": "м. Київ",
                                    "streetAddress": "вул. Банкова, 11, корпус 1"
                                }
                            }
                        ],
                        "value": {
                            "amount": 489,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ]
            }

        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].awards]}

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_award_data, validate_award_operation_not_in_active_status,validate_create_new_award))
    def collection_post(self):
        """Accept or reject bidder application

        Creating new Award
        ------------------

        Example request to create award:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        award = self.request.validated['award']
        tender.awards.append(award)
        if save_tender(self.request):
            self.LOGGER.info('Created tender award {}'.format(award.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_create'}, {'award_id': award.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('{}:Tender Awards'.format(tender.procurementMethodType),
                                                                               tender_id=tender.id, award_id=award['id'])
            return {'data': award.serialize("view")}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the award

        Example request for retrieving the award:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        return {'data': self.request.validated['award'].serialize("view")}

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_patch_award_data, validate_award_operation_not_in_active_status))
    def patch(self):
        """Update of award

        Example request to change the award:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "value": {
                        "amount": 600
                    }
                }
            }

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        award = self.request.context
        award_status = award.status
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if award_status == 'pending' and award.status == 'active':
            tender.contracts.append(type(tender).contracts.model_class({
                'awardID': award.id,
                'suppliers': award.suppliers,
                'date': get_now(),
                'value': award.value,
                'items': tender.items,
                'contractID': '{}-{}{}'.format(tender.tenderID, self.server_id, len(tender.contracts) + 1)}))
            # add_next_award(self.request)
        elif award_status == 'active' and award.status == 'cancelled':
            for i in tender.contracts:
                if i.awardID == award.id:
                    i.status = 'cancelled'
            # add_next_award(self.request)
        elif award_status == 'pending' and award.status == 'unsuccessful':
            pass
            # add_next_award(self.request)
        elif award_status != award.status:
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) status'.format(award_status))
            self.request.errors.status = 403
            raise error_handler(self.request.errors)
        elif award_status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) status'.format(award_status))
            self.request.errors.status = 403
            raise error_handler(self.request.errors)

        if save_tender(self.request):
            self.LOGGER.info('Updated tender award {}'.format(self.request.context.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_patch'}, {'TENDER_REV': tender.rev}))
            return {'data': award.serialize("view")}


@optendersresource(name='negotiation:Tender Awards',
                   collection_path='/tenders/{tender_id}/awards',
                   path='/tenders/{tender_id}/awards/{award_id}',
                   description="Tender awards",
                   procurementMethodType='negotiation')
class TenderNegotiationAwardResource(TenderAwardResource):
    """ Tender Negotiation Award Resource """
    stand_still_delta = timedelta(days=10)

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_award_data, validate_award_operation_not_in_active_status, validate_lot_cancellation, validate_create_new_award_with_lots))
    def collection_post(self):
        """Accept or reject bidder application

        Creating new Award
        ------------------

        Example request to create award:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 201 Created
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 489,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        award = self.request.validated['award']
        award.complaintPeriod = {'startDate': get_now().isoformat()}
        tender.awards.append(award)
        if save_tender(self.request):
            self.LOGGER.info('Created tender award {}'.format(award.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_create'}, {'award_id': award.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('{}:Tender Awards'.format(tender.procurementMethodType),
                                                                               tender_id=tender.id, award_id=award['id'])
            return {'data': award.serialize("view")}

    @json_view(content_type="application/json", permission='edit_tender', validators=(validate_patch_award_data,validate_award_operation_not_in_active_status, validate_lot_cancellation))
    def patch(self):
        """Update of award

        Example request to change the award:

        .. sourcecode:: http

            PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/awards/71b6c23ed8944d688e92a31ec8c3f61a HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "value": {
                        "amount": 600
                    }
                }
            }

        And here is the response to be expected:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Type: application/json

            {
                "data": {
                    "id": "4879d3f8ee2443169b5fbbc9f89fa607",
                    "date": "2014-10-28T11:44:17.947Z",
                    "status": "active",
                    "suppliers": [
                        {
                            "id": {
                                "name": "Державне управління справами",
                                "scheme": "https://ns.openprocurement.org/ua/edrpou",
                                "uid": "00037256",
                                "uri": "http://www.dus.gov.ua/"
                            },
                            "address": {
                                "countryName": "Україна",
                                "postalCode": "01220",
                                "region": "м. Київ",
                                "locality": "м. Київ",
                                "streetAddress": "вул. Банкова, 11, корпус 1"
                            }
                        }
                    ],
                    "value": {
                        "amount": 600,
                        "currency": "UAH",
                        "valueAddedTaxIncluded": true
                    }
                }
            }

        """
        tender = self.request.validated['tender']
        award = self.request.context
        award_status = award.status
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if award.status == "active" and not award.qualified:
            self.request.errors.add('body', 'data', 'Can\'t update award to active status with not qualified')
            self.request.errors.status = 403
            raise error_handler(self.request.errors)
        if award.lotID and \
                [aw.lotID for aw in tender.awards if aw.status in['pending', 'active']].count(award.lotID) > 1:
            self.request.errors.add('body', 'lotID', 'Another award is already using this lotID.')
            self.request.errors.status = 403
            raise error_handler(self.request.errors)
        if award_status == 'pending' and award.status == 'active':
            normalized_end = calculate_normalized_date(get_now(), tender, True)
            award.complaintPeriod.endDate = calculate_business_date(normalized_end, self.stand_still_delta, tender)
            tender.contracts.append(type(tender).contracts.model_class({
                'awardID': award.id,
                'suppliers': award.suppliers,
                'date': get_now(),
                'value': award.value,
                'items': [i for i in tender.items if i.relatedLot == award.lotID],
                'contractID': '{}-{}{}'.format(tender.tenderID, self.server_id, len(tender.contracts) + 1)}))
            # add_next_award(self.request)
        elif award_status == 'active' and award.status == 'cancelled' and any([i.status == 'satisfied' for i in award.complaints]):
            now = get_now()
            cancelled_awards = []
            for i in tender.awards:
                if i.lotID != award.lotID:
                    continue
                if not i.complaintPeriod.endDate or i.complaintPeriod.endDate > now:
                    i.complaintPeriod.endDate = now
                i.status = 'cancelled'
                cancelled_awards.append(i.id)
            for i in tender.contracts:
                if i.awardID in cancelled_awards:
                    i.status = 'cancelled'
        elif award_status == 'active' and award.status == 'cancelled':
            now = get_now()
            if award.complaintPeriod.endDate > now:
                award.complaintPeriod.endDate = now
            for i in tender.contracts:
                if i.awardID == award.id:
                    i.status = 'cancelled'
            # add_next_award(self.request)
        elif award_status == 'pending' and award.status == 'unsuccessful':
            award.complaintPeriod.endDate = get_now()
            # add_next_award(self.request)
        elif award_status == 'unsuccessful' and award.status == 'cancelled' and any([i.status == 'satisfied' for i in award.complaints]):
            now = get_now()
            cancelled_awards = []
            for i in tender.awards:
                if i.lotID != award.lotID:
                    continue
                if not i.complaintPeriod.endDate or i.complaintPeriod.endDate > now:
                    i.complaintPeriod.endDate = now
                i.status = 'cancelled'
                cancelled_awards.append(i.id)
            for i in tender.contracts:
                if i.awardID in cancelled_awards:
                    i.status = 'cancelled'
        elif award_status != award.status:
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) status'.format(award_status))
            self.request.errors.status = 403
            raise error_handler(self.request.errors)
        elif self.request.authenticated_role != 'Administrator' and award_status != 'pending':
            self.request.errors.add('body', 'data', 'Can\'t update award in current ({}) status'.format(award_status))
            self.request.errors.status = 403
            raise error_handler(self.request.errors)

        if save_tender(self.request):
            self.LOGGER.info('Updated tender award {}'.format(self.request.context.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_award_patch'}, {'TENDER_REV': tender.rev}))
            return {'data': award.serialize("view")}


@optendersresource(name='negotiation.quick:Tender Awards',
                   collection_path='/tenders/{tender_id}/awards',
                   path='/tenders/{tender_id}/awards/{award_id}',
                   description="Tender awards",
                   procurementMethodType='negotiation.quick')
class TenderNegotiationQuickAwardResource(TenderNegotiationAwardResource):
    """ Tender Negotiation Quick Award Resource """
    stand_still_delta = timedelta(days=5)
