from odoo.tests import common
import uuid
import logging

_logger = logging.getLogger(__name__)


class WebProgressTest(common.SavepointCase):
    at_install = True
    post_install = False

    def setUp(self):
        super(WebProgressTest, self).setUp()
        self.maxDiff = None
        self.partner_obj = self.env['res.partner']
        self.web_progress_obj = self.env['web.progress']
        self.partner_ids = self.partner_obj
        self.partner_vals = {}
        for idx in range(20):
            self.partner_vals[idx] = dict(name='Test{}'.format(idx),
                                          email='email{}@test.me'.format(idx))
            self.partner_ids |= self.partner_obj.create(dict(self.partner_vals[idx]))

    def _check_web_progress_iter_recordset(self, total, recur_level=0):
        """
        Check that web_progress_iter works correctly for a recordset
        :param total: total number of collection elements
        """
        progress_iter = self.partner_ids[:total].with_progress(msg="Total {} Level {}".format(total,
                                                                                              recur_level))
        self.assertEqual(len(progress_iter), total, msg="Length shall be accessible")
        if total > 0:
            self.assertEqual(progress_iter[0], self.partner_ids[0], msg="Indexing shall be accessible")
            self.assertEqual(progress_iter._name, self.partner_ids._name, msg="Attributes shall be accessible")
        if total == len(self.partner_ids):
            self.assertEqual(progress_iter.ids, self.partner_ids.ids, msg="Attributes shall be accessible")
        count = 0
        for idx, partner_id in zip(range(total),progress_iter):
            self.assertEqual(partner_id.name, self.partner_vals[idx]['name'].format(idx), msg="Wrong name")
            self.assertEqual(partner_id.email, self.partner_vals[idx]['email'].format(idx), msg="Wrong email")
            count += 1
            if recur_level > 0:
                self._check_web_progress_iter_recordset(total, recur_level - 1)
        self.assertEqual(count, total, msg="Not all elements are yielded from a collection")

    def _check_web_progress_iter_recordset_many(self, recur_level=0):
        """
        Iterate recordsets of different lengths
        :param recur_level: recursion level of iterations
        """
        # iterate all partners
        self._check_web_progress_iter_recordset(len(self.partner_ids), recur_level)
        # iterate half of all partners
        self._check_web_progress_iter_recordset(round(len(self.partner_ids)/2), recur_level)
        # iterate again all partners (no recursion)
        self._check_web_progress_iter_recordset(len(self.partner_ids))
        # iterate one partner
        self._check_web_progress_iter_recordset(1, recur_level)
        # iterate empty recordset
        self._check_web_progress_iter_recordset(0, recur_level)

    def _check_web_progress_cancelled(self):
        """
        Checks that the current operation has been cancelled
        """
        code = self.partner_ids._context.get('progress_code', None)
        self.assertIsNotNone(code, msg="Progress code shall be in the context")
        cancelled = self.web_progress_obj._check_cancelled(dict(code=code))
        self.assertTrue(cancelled, msg="Currect operation should have been cancelled")

    def test_web_progress_iter_without_web_progress_code(self):
        """
        Check that web_progress_iter works correctly without a progress_code in context
        """
        self._check_web_progress_iter_recordset_many(0)
        self._check_web_progress_iter_recordset_many(1)

    def test_web_progress_iter_with_web_progress_code(self):
        """
        Check that web_progress_iter works correctly with a progress_code in context
        """
        progress_code = str(uuid.uuid4())
        self.partner_ids = self.partner_ids.with_context(progress_code=progress_code)
        self._check_web_progress_iter_recordset_many(0)
        self._check_web_progress_iter_recordset_many(1)

    def test_web_progress_iter_with_web_progress_code_cancel(self):
        """
        Check that cancel request is respected by web_progress_iter
        """
        progress_code = str(uuid.uuid4())
        self.partner_ids = self.partner_ids.with_context(progress_code=progress_code)
        self._check_web_progress_iter_recordset_many(0)
        self.partner_ids.web_progress_cancel()
        self._check_web_progress_cancelled()
        # any further iteration shall not change a cancelled state
        self._check_web_progress_iter_recordset_many(0)
        self._check_web_progress_cancelled()

    def test_web_progress_percent(self):
        """
        Check web_progress_percent
        """
        progress_code = str(uuid.uuid4())
        self.partner_ids = self.partner_ids.with_context(progress_code=progress_code)
        self.partner_ids.web_progress_percent(0, "Start")
        self.partner_ids.web_progress_percent(50, "Middle")
        self.partner_ids.web_progress_percent(100, "End")
