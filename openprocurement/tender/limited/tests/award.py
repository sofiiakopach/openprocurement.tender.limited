# -*- coding: utf-8 -*-
import unittest

from openprocurement.tender.limited.tests.base import (
    BaseTenderContentWebTest, test_tender_data, test_tender_negotiation_data,
    test_tender_negotiation_quick_data, test_organization, test_lots,
    test_tender_negotiation_data_2items, test_tender_negotiation_quick_data_2items)


class TenderAwardResourceTest(BaseTenderContentWebTest):
    initial_status = 'active'
    initial_data = test_tender_data
    initial_bids = None

    def test_create_tender_award_invalid(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post(request_path, 'data', status=415)
        self.assertEqual(response.status, '415 Unsupported Media Type')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u"Content-Type header should be one of ['application/json']",
             u'location': u'header',
             u'name': u'Content-Type'}
        ])

        response = self.app.post(
            request_path, 'data', content_type='application/json', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'No JSON object could be decoded',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, 'data', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(
            request_path, {'not_data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'data': {
                                      'invalid_field': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Rogue field', u'location':
                u'body', u'name': u'invalid_field'}
        ])

        response = self.app.post_json(request_path, {
                                      'data': {'suppliers': [{'identifier': 'invalid_value'}]}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'identifier': [
                u'Please use a mapping for this field or Identifier instance instead of unicode.']},
                u'location': u'body',
                u'name': u'suppliers'}
        ])

        response = self.app.post_json('/tenders/some_id/awards', {'data': {
                                      'suppliers': [test_organization], 'bid_id': 'some_id'}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/some_id/awards', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        self.set_status('complete')

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization],
                                                'status': 'pending'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create award in current (complete) tender status")

    def test_create_tender_award(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'items': test_tender_data['items'],
                                                              'status': 'pending',
                                                              'qualified': True}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertNotIn('items', award)
        self.assertIn(award['id'], response.headers['Location'])
        self.assertEqual(response.json['data']["subcontractingDetails"], "Details")
        if self.initial_data['procurementMethodType'] == "reporting":
            self.assertNotIn('qualified', award)
        else:
            self.assertEqual(award['qualified'], True)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"description": "description data"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"subcontractingDetails": "subcontractingDetails"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["subcontractingDetails"], "subcontractingDetails")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        # self.assertIn('Location', response.headers)

    def test_canceling_created_award_and_create_new_one(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'status': 'pending'}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award while any (pending) award exists")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'status': 'pending'}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award while any (active) award exists")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')

        # Create new award
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        new_award = response.json['data']
        self.assertEqual(new_award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', new_award)
        self.assertIn(new_award['id'], response.headers['Location'])

        # Add document to new award
        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, new_award['id'], self.tender_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents'.format(self.tender_id, new_award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])

        # patch new award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, new_award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

    def test_patch_tender_award(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': u'pending', "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"items": test_tender_data['items']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.body, u'null')

        response = self.app.patch_json('/tenders/{}/awards/some_id'.format(self.tender_id),
                                       {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id',
                                       {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"awardStatus": "unsuccessful"}},
            status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        # set/update award title
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"title": 'award title'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'award title')
        self.assertNotIn('items', response.json['data'])
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"title": 'award title2'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'award title2')

        # update supplier info
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"suppliers": [{"name": "another supplier"}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['suppliers'][0]['name'], 'another supplier')

        # update value
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"value": {"amount": 499}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['value']['amount'], 499)

        # change status
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        # try to update award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"title": 'award title'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (active) status")

        # patch status for create new award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": 'cancelled'}})
        self.assertEqual(response.status, '200 OK')

        # create new award and test other states
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'status': u'pending', "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'status': u'pending', "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active", 'qualified': True}})
        self.assertEqual(response.status, '200 OK')
        active_award = award

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        # sign contract to complete tender
        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            if i.get('complaintPeriod', {}):  # works for negotiation tender
                i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 2)
        contract = response.json['data'][1]
        self.assertEqual(contract['awardID'], active_award['id'])
        response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
            self.tender_id, contract['id'], self.tender_token),
            {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "unsuccessful"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (complete) tender status")

    def test_patch_tender_award_unsuccessful(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': u'pending', "value": {"amount": 500}}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"title": 'award title'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "cancelled"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (unsuccessful) award status")

    def test_get_tender_award(self):
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(
            self.tender_id, self.tender_token),
            {'data': {'suppliers': [test_organization], 'qualified': True, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        award_data = response.json['data']
        self.assertEqual(award_data, award)

        response = self.app.get('/tenders/{}/awards/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_activate_contract_with_cancelled_award(self):
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(
            self.tender_id, self.tender_token),
            {'data': {'suppliers': [test_organization], 'qualified': True, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.json['data']['status'], 'pending')
        award = response.json['data']

        # Activate award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Get contract
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        contract = response.json['data'][0]

        # Cancel award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {'data': {'status': 'cancelled'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Try to sign in contract
        response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
            self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can\'t update contract in current (cancelled) status")


class TenderAwardComplaintResourceTest(BaseTenderContentWebTest):
    initial_status = 'active'
    initial_data = test_tender_data
    initial_bids = None

    def test_create_tender_award_complaints(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}}, status=404)
        self.assertEqual(response.status, '404 Not Found')


class TenderNegotiationAwardResourceTest(TenderAwardResourceTest):
    initial_data = test_tender_negotiation_data

    def test_patch_tender_award_Administrator_change(self):
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(
            self.tender_id, self.tender_token), {'data': {'suppliers': [test_organization], 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        complaintPeriod = award['complaintPeriod'][u'startDate']

        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(self.tender_id, award['id']),
                                       {"data": {"complaintPeriod": {"endDate": award['complaintPeriod'][u'startDate']}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("endDate", response.json['data']['complaintPeriod'])
        self.assertEqual(response.json['data']['complaintPeriod']["endDate"], complaintPeriod)

        self.app.authorization = authorization
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active", 'qualified': True}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}'.format(
            self.tender_id, award['id']),
            {"data": {"complaintPeriod": {"endDate": award['complaintPeriod'][u'startDate']}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertIn("endDate", response.json['data']['complaintPeriod'])
        self.assertEqual(response.json['data']['complaintPeriod']["endDate"], complaintPeriod)

    def test_patch_active_not_qualified(self):
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])
        self.assertEqual(response.json['data']["subcontractingDetails"], "Details")

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, award['id'], self.tender_token),
                                       {'data': {'status': 'active'}},
                                       status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award to active status with not qualified")

    def test_create_two_awards_on_one_lot(self):
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                       {"data": {"items": [{'relatedLot': lot['id']}]}})
        self.assertEqual(response.status, '200 OK')

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending',
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending',
                                                              'lotID': lot['id']}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award on lot while any (pending) award exists")


class TenderNegotiationLotAwardResourceTest(TenderAwardResourceTest):
    initial_data = test_tender_negotiation_data

    def test_create_award_with_lot(self):
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']
        self.assertEqual(lot['value']['currency'], "UAH")

        # try create without lotID field
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending',
                                                              'qualified': True}},
                                      status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [{"location": "body",
                                                    "name": "lotID",
                                                    "description": ["This field is required."]}
                                                   ])
        # send with lotID
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending',
                                                              'qualified': True,
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        # check fields
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])
        self.assertEqual(response.json['data']["subcontractingDetails"], "Details")
        if self.initial_data['procurementMethodType'] == "reporting":
            self.assertNotIn('qualified', award)
        else:
            self.assertEqual(award['qualified'], True)

        # get award which we create before
        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

    def test_create_tender_award_with_lot(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'subcontractingDetails': 'Details',
                                                              'status': 'pending',
                                                              'qualified': True,
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])
        self.assertIn(award['lotID'], lot['id'])
        self.assertEqual(response.json['data']["subcontractingDetails"], "Details")
        if self.initial_data['procurementMethodType'] == "reporting":
            self.assertNotIn('qualified', award)
        else:
            self.assertEqual(award['qualified'], True)

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"description": "description data"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"subcontractingDetails": "subcontractingDetails"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["subcontractingDetails"], "subcontractingDetails")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')
        # self.assertIn('Location', response.headers)

    def test_canceling_created_award_and_create_new_one(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        # create award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': 'pending',
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.assertEqual(award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', award)
        self.assertIn(award['id'], response.headers['Location'])

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][-1], award)

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'status': 'pending',
                                                'lotID': lot['id']}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award on lot while any (pending) award exists")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'status': 'pending',
                                                'lotID': lot['id']}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award on lot while any (active) award exists")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'cancelled')

        # Create new award

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': 'pending',
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        new_award = response.json['data']
        self.assertEqual(new_award['suppliers'][0]['name'], test_organization['name'])
        self.assertIn('id', new_award)
        self.assertIn(new_award['id'], response.headers['Location'])

        # Add document to new award
        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, new_award['id'], self.tender_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents'.format(self.tender_id, new_award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])

        # patch new award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, new_award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], u'active')

    def test_patch_tender_award(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True, 'status': u'pending',
                                                              "value": {"amount": 500}, "lotID": lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"items": test_tender_data['items']}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.body, u'null')

        response = self.app.patch_json('/tenders/{}/awards/some_id'.format(self.tender_id),
                                       {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id',
                                       {"data": {"status": "unsuccessful"}}, status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"awardStatus": "unsuccessful"}},
            status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'], [
            {"location": "body", "name": "awardStatus", "description": "Rogue field"}
        ])

        # set/update award title
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"title": 'award title'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'award title')
        self.assertNotIn('items', response.json['data'])
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"title": 'award title2'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['title'], 'award title2')

        # update supplier info
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"suppliers": [{"name": "another supplier"}]}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['suppliers'][0]['name'], 'another supplier')

        # update value
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"value": {"amount": 499}}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['value']['amount'], 499)

        # change status
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        # try to update award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"title": 'award title'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update award in current (active) status")

        # patch status for create new award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": 'cancelled'}})
        self.assertEqual(response.status, '200 OK')

        # create new award and test other states
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending',
                                                              "value": {"amount": 500}, "lotID": lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "pending"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'status': u'pending',
                                                              "value": {"amount": 500}, "lotID": lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active", 'qualified': True}})
        self.assertEqual(response.status, '200 OK')
        active_award = award

        response = self.app.get(request_path)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(len(response.json['data']), 3)

        # sign contract to complete tender
        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            if i.get('complaintPeriod', {}):  # works for negotiation tender
                i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)
        response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 2)
        contract = response.json['data'][1]
        self.assertEqual(contract['awardID'], active_award['id'])
        response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
            self.tender_id, contract['id'], self.tender_token),
            {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["value"]["amount"], 500)

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "active"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (complete) tender status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token),
            {"data": {"status": "unsuccessful"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (complete) tender status")

    def test_patch_tender_award_unsuccessful(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']
        # create award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': u'pending', "value": {"amount": 500},
                                                              'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"title": 'award title'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), {"data": {"status": "cancelled"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update award in current (unsuccessful) status")

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, award['id'], self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (unsuccessful) award status")

    def test_get_tender_award(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(
            self.tender_id, self.tender_token),
            {'data': {'suppliers': [test_organization], 'qualified': True, 'status': 'pending', 'lotID': lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}'.format(self.tender_id, award['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        award_data = response.json['data']
        self.assertEqual(award_data, award)

        response = self.app.get('/tenders/{}/awards/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_two_lot_two_awards(self):
        self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                            {'data': {'items': test_tender_negotiation_data['items'] * 2}})

        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot1 = response.json['data']
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot2 = response.json['data']
        self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                            {'data': {'items': [{'relatedLot': lot1['id']},
                                                {'relatedLot': lot2['id']}]
                                      }
                             })
        # create first award
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'subcontractingDetails': 'Details',
                                                'status': 'pending', 'qualified': True, 'lotID': lot1['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        # create second award
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'subcontractingDetails': 'Details',
                                                'status': 'pending', 'qualified': True, 'lotID': lot2['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')

        # try create another awards
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'subcontractingDetails': 'Details',
                                                'status': 'pending', 'qualified': True, 'lotID': lot1['id']}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award on lot while any (pending) award exists")

        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization], 'subcontractingDetails': 'Details',
                                                'status': 'pending', 'qualified': True, 'lotID': lot2['id']}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't create new award on lot while any (pending) award exists")

        lots = self.app.get('/tenders/{}/lots?acc_token{}'.format(self.tender_id, self.tender_token)).json['data']

        # try create another lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add lot when you have awards")

        response = self.app.get('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), len(lots))


class TenderNegotiationQuickAwardResourceTest(TenderNegotiationAwardResourceTest):
    initial_data = test_tender_negotiation_quick_data


class TenderNegotiationAwardComplaintResourceTest(BaseTenderContentWebTest):
    initial_data = test_tender_negotiation_data

    def create_award(self):
        # Create award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

    def setUp(self):
        super(TenderNegotiationAwardComplaintResourceTest, self).setUp()
        self.create_award()

    def test_create_tender_award_complaint_invalid(self):
        response = self.app.post_json('/tenders/some_id/awards/some_id/complaints',
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}},
                                      status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
        ])

        request_path = '/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id)

        response = self.app.post(request_path, 'data', status=415)
        self.assertEqual(response.status, '415 Unsupported Media Type')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u"Content-Type header should be one of ['application/json']",
             u'location': u'header',
             u'name': u'Content-Type'}
        ])

        response = self.app.post(
            request_path, 'data', content_type='application/json', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'No JSON object could be decoded',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, 'data', status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(
            request_path, {'not_data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Data not available',
                u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json(request_path, {'data': {}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'author'},
            {u'description': [u'This field is required.'], u'location': u'body', u'name': u'title'},
        ])

        response = self.app.post_json(request_path, {'data': {'invalid_field': 'invalid_value'}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Rogue field', u'location':
                u'body', u'name': u'invalid_field'}
        ])

        response = self.app.post_json(request_path, {
                                      'data': {'author': {'identifier': 'invalid_value'}}}, status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'identifier': [
                u'Please use a mapping for this field or Identifier instance instead of unicode.']},
                u'location': u'body', u'name': u'author'}
        ])

        response = self.app.post_json(request_path,
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': {'identifier': {'id': 0}}}},
                                      status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'],
                              u'identifier': {u'scheme': [u'This field is required.']},
                              u'name': [u'This field is required.'],
                              u'address': [u'This field is required.']},
             u'location': u'body',
             u'name': u'author'}
        ])

        response = self.app.post_json(request_path,
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': {'name': 'name', 'identifier': {'uri': 'invalid_value'}}}},
                                      status=422)
        self.assertEqual(response.status, '422 Unprocessable Entity')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': {u'contactPoint': [u'This field is required.'],
                              u'identifier': {u'scheme': [u'This field is required.'],
                                              u'id': [u'This field is required.'],
                                              u'uri': [u'Not a well formed URL.']},
                              u'address': [u'This field is required.']},
             u'location': u'body',
             u'name': u'author'}
        ])

    def test_create_tender_award_complaints(self):

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id,
                                                                                   self.tender_token),
            {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")


        self.create_award()


        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add complaint in current (unsuccessful) tender status")

    def test_patch_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {"data": {"status": "cancelled", "cancellationReason": "reason"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Forbidden")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "active")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {"title": "claim title"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["title"], "claim title")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {"status": "pending"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "pending")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], owner_token),
            {"data": {"status": "stopping", "cancellationReason": "reason"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "stopping")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id),
                                       {"data": {"status": "resolved", "resolution": "resolution text"}},
                                       status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.patch_json('/tenders/some_id/awards/some_id/complaints/some_id',
                                       {"data": {"status": "resolved", "resolution": "resolution text"}},
                                       status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], owner_token),
            {"data": {"status": "cancelled", "cancellationReason": "reason"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint")

        response = self.app.patch_json('/tenders/{}/awards/some_id/complaints/some_id'.format(self.tender_id),
                                       {"data": {"status": "resolved", "resolution": "resolution text"}},
                                       status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], "stopping")
        self.assertEqual(response.json['data']["cancellationReason"], "reason")

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, complaint['id'], owner_token),
            {"data": {"status": "claim"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update complaint in current (complete) tender status")

    def test_review_tender_award_complaint(self):
        for status in ['invalid', 'declined', 'satisfied']:
            self.app.authorization = ('Basic', ('broker', ''))
            response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                          {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                    'author': test_organization, 'status': 'pending'}})
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            complaint = response.json['data']

            self.app.authorization = ('Basic', ('reviewer', ''))
            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                self.tender_id, self.award_id, complaint['id']), {"data": {"decision": '{} complaint'.format(status)}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["decision"], '{} complaint'.format(status))

            if status != "invalid":
                response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                    self.tender_id, self.award_id, complaint['id']), {"data": {"status": "accepted"}})
                self.assertEqual(response.status, '200 OK')
                self.assertEqual(response.content_type, 'application/json')
                self.assertEqual(response.json['data']["status"], "accepted")

                response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                    self.tender_id, self.award_id, complaint['id']),
                    {"data": {"decision": 'accepted:{} complaint'.format(status)}})
                self.assertEqual(response.status, '200 OK')
                self.assertEqual(response.content_type, 'application/json')
                self.assertEqual(response.json['data']["decision"], 'accepted:{} complaint'.format(status))

            response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
                self.tender_id, self.award_id, complaint['id']),
                {"data": {"status": status}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], status)

    def test_get_tender_award_complaint(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], complaint)

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id'.format(self.tender_id, self.award_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_award_complaints(self):
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        response = self.app.get('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], complaint)

        response = self.app.get('/tenders/some_id/awards/some_id/complaints', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        tender = self.db.get(self.tender_id)
        for i in tender.get('awards', []):
            i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
        self.db.save(tender)

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")

    def test_cancelled_award_with_complaint(self):
        """ When complaint on award in satisfied status and owner cancel award,
            then all awards and contracts must move to status cancelled """

        # Move award to unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')
        self.old_award_id = self.award_id

        # Create another award
        self.create_award()

        # Activate award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'active'}})

        # Create complaint
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        # Move complaint to satisfied
        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']),
            {'data': {'status': 'accepted'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'accepted')

        # Make decision
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']), {"data": {"decision": 'satisfied complaint'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], 'satisfied complaint')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {'data': {'status': 'satisfied'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'satisfied')

        # Active award and then cancel it
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Let's check another award
        # From unsuccessful move to cancelled
        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.old_award_id, self.tender_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # And check contracts
        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['status'], 'cancelled')


class TenderLotNegotiationAwardComplaintResourceTest(TenderNegotiationAwardComplaintResourceTest):

    def test_create_tender_award_complaints(self):
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id,
                                                                                   self.tender_token),
            {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in complaintPeriod")

        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.lot_id}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        self.assertEqual(complaint['author']['name'], test_organization['name'])
        self.assertIn('id', complaint)
        self.assertIn(complaint['id'], response.headers['Location'])


        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id,
                                                                                   self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'active')

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id,
                                                                                   self.tender_token), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], 'cancelled')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can add complaint only in complaintPeriod")

        response = self.app.get('/tenders/{}'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], 'active')

        self.set_status('unsuccessful')

        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}},
                                      status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add complaint in current (unsuccessful) tender status")

    def create_award(self):
        # create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.lot = response.json['data']
        self.lot_id = self.lot['id']

        # set items to lot
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                       {
                                           "data": {
                                               "items": [
                                                   {
                                                       "relatedLot": self.lot['id']
                                                   }
                                               ]
                                           }
                                       })
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['items'][0]['relatedLot'], self.lot['id'])

        # create award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

    def test_cancelled_award_with_complaint(self):
        """ When complaint on award in satisfied status and owner cancel award,
            then all awards (with same lotID) and contracts must move to status cancelled """

        # Move award to unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})
        self.old_award_id = self.award_id
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

        # Create another award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

        # Activate award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'active'}})

        # Create complaint
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        # Move complaint to satisfied
        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']),
            {'data': {'status': 'accepted'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'accepted')

        # Make decision
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']), {"data": {"decision": 'satisfied complaint'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], 'satisfied complaint')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {'data': {'status': 'satisfied'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'satisfied')

        # Active award and then cancel it
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Let's check another award

        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')
        self.assertEqual(response.json['data']['lotID'], self.lot['id'])

        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.old_award_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')
        self.assertEqual(response.json['data']['lotID'], self.lot['id'])

        # And check contracts
        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['status'], 'cancelled')


class Tender2LotNegotiationAwardComplaintResourceTest(BaseTenderContentWebTest):
    initial_data = test_tender_negotiation_data_2items

    def setUp(self):
        super(Tender2LotNegotiationAwardComplaintResourceTest, self).setUp()
        self.create_award()

    def create_award(self):
        # create lots
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.first_lot = response.json['data']

        self.assertEqual(response.content_type, 'application/json')
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.second_lot = response.json['data']

        # set items to lot
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                       {
                                           "data": {
                                               "items": [
                                                   {"relatedLot": self.first_lot['id']},
                                                   {"relatedLot": self.second_lot['id']}
                                               ]
                                           }
                                       })

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['items'][0]['relatedLot'], self.first_lot['id'])
        self.assertEqual(response.json['data']['items'][1]['relatedLot'], self.second_lot['id'])

        # create first award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.first_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.first_award = response.json['data']
        self.award_id = self.first_award['id']

        # create second award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.second_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.second_award = response.json['data']
        self.second_award_id = self.second_award['id']

    def test_cancelled_award_with_complaint(self):
        """ When complaint on award in satisfied status and owner cancel award,
            then all awards (with same lotID) and contracts must move to status cancelled """

        # Move first award to unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

        # Create another award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.first_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

        # Activate first award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'active'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Activate second award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'active'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Create complaint on first award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        # Move complaint to satisfied
        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']),
            {'data': {'status': 'accepted'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'accepted')

        # Make decision
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']), {"data": {"decision": 'satisfied complaint'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], 'satisfied complaint')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {'data': {'status': 'satisfied'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'satisfied')

        # Active award and then cancel it
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Let's awards

        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.first_award['id'], self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['lotID'], self.first_award['lotID'])
        self.assertEqual(response.json['data']['status'], 'cancelled')

        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award['id'], self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['lotID'], self.second_award['lotID'])
        self.assertEqual(response.json['data']['status'], 'active')

        # And check contracts
        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')

        for contract in response.json['data']:
            if contract['awardID'] == self.second_award['id']:
                self.assertEqual(contract['status'], 'pending')

    def test_cancelled_active_award_with_complaint(self):
        """ When complaint on award in satisfied status and owner cancel award,
            then all awards (with same lotID) and contracts must move to status cancelled """

        # Activate first award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'active'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Activate second award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'active'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Create complaint on first award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        # Move complaint to satisfied
        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']),
            {'data': {'status': 'accepted'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'accepted')

        # Make decision
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']), {"data": {"decision": 'satisfied complaint'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], 'satisfied complaint')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {'data': {'status': 'satisfied'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'satisfied')

        # Active award and then cancel it
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Let's check another award

        response = self.app.get('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.second_award['id'], self.tender_token))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')
        self.assertEqual(response.json['data']['lotID'], self.second_award['lotID'])

        # And check contracts
        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
        self.assertEqual(response.status, '200 OK')

        for contract in response.json['data']:
            if contract['awardID'] == self.first_award['id']:
                self.assertEqual(contract['status'], 'cancelled')
            if contract['awardID'] == self.second_award['id']:
                self.assertEqual(contract['status'], 'pending')

    def test_cancelled_unsuccessful_award_with_complaint(self):
        """ When complaint on award in satisfied status and owner cancel award,
            then all awards (with same lotID) and contracts must move to status cancelled """

        # Move first award to unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

        # Create another award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.first_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']

        # Activate second award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'active'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Create complaint on first award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title', 'description': 'complaint description',
                                                'author': test_organization, 'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        # Move complaint to satisfied
        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']),
            {'data': {'status': 'accepted'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'accepted')

        # Make decision
        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id']), {"data": {"decision": 'satisfied complaint'}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], 'satisfied complaint')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}'.format(
            self.tender_id, self.award_id, complaint['id'], self.tender_token),
            {'data': {'status': 'satisfied'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'satisfied')

        # Move to unsuccessful award
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')
        # Cancel award
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Let's check another award
        response = self.app.get('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        for award in response.json['data']:
            if award['lotID'] == self.first_award['lotID']:
                self.assertEqual(award['status'], 'cancelled')
            else:
                self.assertEqual(award['status'], 'active')

        # And check contracts
        response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(response.json['data'][0]['status'], 'pending')


class Tender2LotNegotiationQuickAwardComplaintResourceTest(Tender2LotNegotiationAwardComplaintResourceTest):
    initial_data = test_tender_negotiation_quick_data_2items


class Tender2LotNegotiationAwardComplaintResourceTest(BaseTenderContentWebTest):
    initial_data = test_tender_negotiation_data_2items

    def setUp(self):
        super(Tender2LotNegotiationAwardComplaintResourceTest, self).setUp()
        self.create_award()

    def create_award(self):
        # create lots
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.first_lot = response.json['data']

        self.assertEqual(response.content_type, 'application/json')
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})
        self.assertEqual(response.status, '201 Created')
        self.second_lot = response.json['data']

        # set items to lot
        response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                       {
                                           "data": {
                                               "items": [
                                                   {"relatedLot": self.first_lot['id']},
                                                   {"relatedLot": self.second_lot['id']}
                                               ]
                                           }
                                       })

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['items'][0]['relatedLot'], self.first_lot['id'])
        self.assertEqual(response.json['data']['items'][1]['relatedLot'], self.second_lot['id'])

        # create first award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.first_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.first_award = response.json['data']
        self.award_id = self.first_award['id']

        # create second award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization], 'qualified': True,
                                                              'status': 'pending', 'lotID': self.second_lot['id']}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.second_award = response.json['data']
        self.second_award_id = self.second_award['id']

    def test_two_awards_on_one_lot(self):
        """ Create two award and move second on first lot """

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}},
            status=403)

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'], [{"location": "body",
                                                    "name": "lotID",
                                                    "description": "Another award is already using this lotID."}])

    def test_change_lotID_from_unsuccessful_award(self):
        """ Create two award, and then try change lotId when
            award in status unsuccessful """

        # Make award unsuccessful
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'unsuccessful'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'unsuccessful')

        # Move award on another lot
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['lotID'], self.second_lot['id'])

    def test_change_lotID_from_active_award(self):
        """ Create two  award, and then change lotID when
            award in status active """
        # Try set lotID while another award has status pending
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}},
            status=403)

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'], [{"location": "body",
                                                    "name": "lotID",
                                                    "description": "Another award is already using this lotID."}])

        # Make award active
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'active'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')

        # Move award on another lot
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}},
            status=403)

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'], [{"location": "body",
                                                    "name": "lotID",
                                                    "description": "Another award is already using this lotID."}])

    def test_change_lotID_from_cancelled_award(self):
        """ Create two award, and then change lotID when
            award in status cancelled """
        # active second award
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'active'}})

        # Try set lotID while another award has status active
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}},
            status=403)

        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'], [{"location": "body",
                                                    "name": "lotID",
                                                    "description": "Another award is already using this lotID."}])

        # Make award cancelled
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.second_award_id, self.tender_token),
            {'data': {'status': 'cancelled'}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'cancelled')

        # Move award on another lot
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            {'data': {'lotID': self.second_lot['id']}})

        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['lotID'], self.second_lot['id'])


class Tender2LotNegotiationQuickAwardComplaintResourceTest(Tender2LotNegotiationAwardComplaintResourceTest):
    initial_data = test_tender_negotiation_quick_data_2items


class TenderNegotiationQuickAwardComplaintResourceTest(TenderNegotiationAwardComplaintResourceTest):
    initial_data = test_tender_negotiation_quick_data


class TenderLotNegotiationQuickAwardComplaintResourceTest(TenderLotNegotiationAwardComplaintResourceTest):
    initial_data = test_tender_negotiation_quick_data


class TenderNegotiationAwardComplaintDocumentResourceTest(BaseTenderContentWebTest):
    initial_data = test_tender_negotiation_data

    def setUp(self):
        super(TenderNegotiationAwardComplaintDocumentResourceTest, self).setUp()
        # Create award
        # Create award
        request_path = '/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token)
        response = self.app.post_json(request_path, {'data': {'suppliers': [test_organization],
                                                              'qualified': True,
                                                              'status': 'pending'}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        award = response.json['data']
        self.award_id = award['id']
        # Create complaint for award
        response = self.app.post_json('/tenders/{}/awards/{}/complaints'.format(self.tender_id, self.award_id),
                                      {'data': {'title': 'complaint title',
                                                'description': 'complaint description',
                                                'author': test_organization}})
        complaint = response.json['data']
        self.complaint_id = complaint['id']
        self.complaint_owner_token = response.json['access']['token']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/awards/some_id/complaints/some_id/documents',
                                 status=404,
                                 upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/awards/some_id/complaints/some_id/documents'.format(self.tender_id),
                                 status=404,
                                 upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/complaints/some_id/documents'.format(
            self.tender_id, self.award_id),
            status=404,
            upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.tender_token),
            status=404,
            upload_files=[('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/complaints/some_id/documents'.format(self.tender_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id/documents'.format(self.tender_id,
                                                                                            self.award_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.tender_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/some_id/documents/some_id'.format(self.tender_id,
                                                                                                    self.award_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/some_id'.format(
            self.tender_id, self.award_id, self.complaint_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/awards/some_id/complaints/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/awards/some_id/complaints/some_id/documents/some_id'.format(self.tender_id),
                                status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/some_id/documents/some_id'.format(
            self.tender_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'complaint_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/some_id'.format(
            self.tender_id, self.award_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (draft) complaint status")

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token),
            upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents'.format(
            self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents?all=true'.format(
            self.tender_id, self.award_id, self.complaint_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (complete) tender status")

    def test_put_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token),
            upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.tender_token),
            status=404,
            upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content2')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token),
            upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token),
            'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token),
            upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document in current (complete) tender status")

    def test_patch_tender_award_complaint_document(self):
        response = self.app.post('/tenders/{}/awards/{}/complaints/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token),
            upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.tender_token),
            {"data": {"description": "document description"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token),
            {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, self.complaint_owner_token),
            {"data": {"status": "pending"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']["status"], "pending")

        response = self.app.put('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token), 'contentX', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/complaints/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'contentX')
        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.complaint_id, doc_id, self.complaint_owner_token),
            {"data": {"description": "document description"}},
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document in current (complete) tender status")


class TenderNegotiationQuickAwardComplaintDocumentResourceTest(TenderNegotiationAwardComplaintDocumentResourceTest):
    initial_data = test_tender_negotiation_quick_data


class TenderAwardDocumentResourceTest(BaseTenderContentWebTest):
    initial_status = 'active'
    initial_data = test_tender_data
    initial_bids = None

    def setUp(self):
        super(TenderAwardDocumentResourceTest, self).setUp()
        # Create award
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization],
                                                'qualified': True,
                                                'status': 'pending'}})
        award = response.json['data']
        self.award_id = award['id']

    def test_not_found(self):
        response = self.app.post('/tenders/some_id/awards/some_id/documents',
                                 status=404,
                                 upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.post('/tenders/{}/awards/some_id/documents'.format(self.tender_id),
                                 status=404,
                                 upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            status=404,
            upload_files=[('invalid_value', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'body', u'name': u'file'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/documents', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/documents'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/some_id/awards/some_id/documents/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.get('/tenders/{}/awards/some_id/documents/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/documents/some_id'.format(self.tender_id, self.award_id),
                                status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'document_id'}
        ])

        response = self.app.put('/tenders/some_id/awards/some_id/documents/some_id', status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

        response = self.app.put('/tenders/{}/awards/some_id/documents/some_id'.format(self.tender_id), status=404,
                                upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'award_id'}
        ])

        response = self.app.put('/tenders/{}/awards/{}/documents/some_id'.format(
            self.tender_id, self.award_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
        ])

    def test_create_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])
        self.assertEqual('name.doc', response.json["data"]["title"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents?all=true'.format(self.tender_id, self.award_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"][0]["id"])
        self.assertEqual('name.doc', response.json["data"][0]["title"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?download=some_id'.format(
            self.tender_id, self.award_id, doc_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
        ])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 7)
        self.assertEqual(response.body, 'content')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        self.set_status('complete')

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (complete) tender status")

    def test_create_tender_award_document_invalid(self):
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (active) award status")

        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token), {"data": {"status": "cancelled"}})
        self.assertEqual(response.status, '200 OK')

        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token),
            upload_files=[('file', 'name.doc', 'content')],
            status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't add document in current (cancelled) award status")

    def test_put_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
            self.tender_id, self.award_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token),
            status=404,
            upload_files=[('invalid_name', 'name.doc', 'content')])
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location': u'body', u'name': u'file'}])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content2')])
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content2')

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('name.doc', response.json["data"]["title"])

        response = self.app.put('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token), 'content3', content_type='application/msword')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        key = response.json["data"]["url"].split('?')[-1]

        response = self.app.get('/tenders/{}/awards/{}/documents/{}?{}'.format(
            self.tender_id, self.award_id, doc_id, key))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/msword')
        self.assertEqual(response.content_length, 8)
        self.assertEqual(response.body, 'content3')

        self.set_status('complete')

        response = self.app.put('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document in current (complete) tender status")

    def test_patch_tender_award_document(self):
        response = self.app.post('/tenders/{}/awards/{}/documents?acc_token={}'.format(
           self.tender_id, self.award_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        doc_id = response.json["data"]['id']
        self.assertIn(doc_id, response.headers['Location'])

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token),
            {"data": {"description": "document description"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])

        response = self.app.get('/tenders/{}/awards/{}/documents/{}'.format(
            self.tender_id, self.award_id, doc_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(doc_id, response.json["data"]["id"])
        self.assertEqual('document description', response.json["data"]["description"])

        self.set_status('complete')

        response = self.app.patch_json('/tenders/{}/awards/{}/documents/{}?acc_token={}'.format(
            self.tender_id, self.award_id, doc_id, self.tender_token),
            {"data": {"description": "document description"}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"],
                         "Can't update document in current (complete) tender status")


class TenderAwardNegotiationDocumentResourceTest(TenderAwardDocumentResourceTest):
    initial_data = test_tender_negotiation_data


class TenderAwardNegotiationQuickDocumentResourceTest(TenderAwardNegotiationDocumentResourceTest):
    initial_data = test_tender_negotiation_quick_data


class TenderLotAwardNegotiationDocumentResourceTest(TenderAwardNegotiationDocumentResourceTest):

    def setUp(self):
        super(TenderAwardDocumentResourceTest, self).setUp()
        # Create lot
        response = self.app.post_json('/tenders/{}/lots?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': test_lots[0]})

        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        lot = response.json['data']
        # Create award
        response = self.app.post_json('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token),
                                      {'data': {'suppliers': [test_organization],
                                                'qualified': True,
                                                'status': 'pending',
                                                'lotID': lot['id']}})
        award = response.json['data']
        self.award_id = award['id']


class TenderLotAwardNegotiationQuickDocumentResourceTest(TenderLotAwardNegotiationDocumentResourceTest):
    initial_data = test_tender_negotiation_quick_data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderAwardDocumentResourceTest))
    suite.addTest(unittest.makeSuite(TenderAwardResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
