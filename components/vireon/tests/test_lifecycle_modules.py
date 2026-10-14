from datetime import datetime, timezone
import unittest
from vireon.ai_guard import ModelSpec, assess_model
from vireon.digital_measures import validate_digital_measure
from vireon.lifecycle import simulate_lifecycle
from vireon.trial_integrity import TrialEvent, assess_site

class LifecycleModuleTests(unittest.TestCase):
    def test_model_guard_no_flags_for_stable_data(self):
        r=assess_model(ModelSpec("m","1","research","low","validated"),[100,101,99],[100,101,99])
        self.assertEqual(r.status,"monitor")
    def test_measure_range_flag(self):
        self.assertIn("above_expected_range",validate_digital_measure("m",[1,2,9],expected_max=5).flags)
    def test_site_missingness_flag(self):
        now=datetime.now(timezone.utc)
        events=[TrialEvent(str(i),"S",now,"visit",complete=(i!=0)) for i in range(10)]
        self.assertIn("missing_data_pattern",assess_site("S",events).flags)
    def test_lifecycle_order(self):
        result=simulate_lifecycle("C")
        self.assertEqual(result[0].stage.value,"discovery"); self.assertEqual(result[-1].stage.value,"post_market")

if __name__=="__main__": unittest.main()
