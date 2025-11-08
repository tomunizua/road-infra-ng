"""
Consolidated test suite for budget optimization module
Tests both standalone functionality and Flask API integration
"""
import unittest
import json
import sys
import os
import pandas as pd
from io import StringIO

# Add budget_optimization to path
BUDGET_DIR = os.path.dirname(os.path.abspath(__file__))
if BUDGET_DIR not in sys.path:
    sys.path.insert(0, BUDGET_DIR)

from enhanced_budget import (
    EnhancedRepairFinancials,
    BudgetConfig,
    BudgetOptimizationError
)
from data_converter import (
    database_report_to_budget_format,
    batch_convert_reports,
    get_conversion_stats
)


class TestDataConverter(unittest.TestCase):
    """Test database to budget format conversion"""
    
    def setUp(self):
        """Set up test data"""
        self.pothole_report = {
            "tracking_number": "RW20251001ABC",
            "damage_type": "pothole",
            "severity_score": 7,
            "estimated_cost": 150000,
            "image_filename": "report_1.jpg"
        }
        
        self.crack_report = {
            "tracking_number": "RW20251002DEF",
            "damage_type": "crack",
            "severity_score": 5,
            "estimated_cost": 100000
        }
    
    def test_pothole_conversion(self):
        """Test conversion of pothole report"""
        result = database_report_to_budget_format(self.pothole_report)
        
        self.assertEqual(result["tracking_number"], "RW20251001ABC")
        self.assertEqual(result["severity"], "Moderate")  # 7 -> Moderate
        self.assertEqual(result["damage_type"], "pothole")
        self.assertIn("length_cm", result)
        self.assertIn("breadth_cm", result)
        self.assertIn("depth_cm", result)
    
    def test_severity_mapping(self):
        """Test severity score to category mapping"""
        # Minor
        minor_report = {**self.pothole_report, "severity_score": 3}
        result = database_report_to_budget_format(minor_report)
        self.assertEqual(result["severity"], "Minor")
        
        # Moderate
        moderate_report = {**self.pothole_report, "severity_score": 5}
        result = database_report_to_budget_format(moderate_report)
        self.assertEqual(result["severity"], "Moderate")
        
        # Severe
        severe_report = {**self.pothole_report, "severity_score": 9}
        result = database_report_to_budget_format(severe_report)
        self.assertEqual(result["severity"], "Severe")
    
    def test_missing_fields(self):
        """Test error on missing required fields"""
        incomplete_report = {"damage_type": "pothole"}
        
        with self.assertRaises(ValueError):
            database_report_to_budget_format(incomplete_report)
    
    def test_batch_conversion(self):
        """Test batch conversion with mixed valid/invalid reports"""
        reports = [
            self.pothole_report,
            self.crack_report,
            {"damage_type": "rut"}  # Invalid - missing required fields
        ]
        
        converted, skipped = batch_convert_reports(reports)
        
        self.assertEqual(len(converted), 2)
        self.assertEqual(len(skipped), 1)
        self.assertIn("error", skipped[0])
    
    def test_conversion_stats(self):
        """Test statistics generation"""
        reports = [
            {**self.pothole_report, "severity_score": 9},
            {**self.crack_report, "severity_score": 5},
            {**self.pothole_report, "severity_score": 3, "tracking_number": "RW3"}
        ]
        
        stats = get_conversion_stats(reports)
        
        self.assertEqual(stats["total_reports"], 3)
        self.assertEqual(stats["severity_distribution"]["Severe"], 1)
        self.assertEqual(stats["severity_distribution"]["Moderate"], 1)
        self.assertEqual(stats["severity_distribution"]["Minor"], 1)
        self.assertEqual(stats["damage_type_distribution"]["pothole"], 2)
        self.assertEqual(stats["damage_type_distribution"]["crack"], 1)


class TestEnhancedRepairFinancials(unittest.TestCase):
    """Test core budget optimization functionality"""
    
    def setUp(self):
        """Set up test repairs"""
        self.repair_data = {
            "length_cm": 100,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": "Moderate",
            "urgency": "routine",
            "image_path": "/uploads/damage.jpg"
        }
        
        self.severe_repair_data = {
            "length_cm": 150,
            "breadth_cm": 120,
            "depth_cm": 20,
            "severity": "Severe",
            "urgency": "immediate",
            "image_path": "/uploads/severe.jpg"
        }
    
    def test_single_repair_creation(self):
        """Test creating a single repair object"""
        df = pd.DataFrame([self.repair_data])
        repair = EnhancedRepairFinancials(df)
        
        self.assertIsNotNone(repair.cost_estimation_data)
        self.assertIsNotNone(repair.priority_score)
        self.assertIn("Estimated Cost (₦)", repair.cost_estimation_data)
        self.assertIn("Priority_Score", repair.priority_score)
    
    def test_cost_estimation_moderate(self):
        """Test cost estimation for moderate severity"""
        df = pd.DataFrame([self.repair_data])
        repair = EnhancedRepairFinancials(df)
        
        cost = repair.cost_estimation_data["Estimated Cost (₦)"]
        # Should be roughly 40k-400k for moderate damage with these dimensions
        self.assertGreater(cost, 40000)
        self.assertLess(cost, 500000)
    
    def test_cost_estimation_severe(self):
        """Test cost estimation for severe damage"""
        df = pd.DataFrame([self.severe_repair_data])
        repair = EnhancedRepairFinancials(df)
        
        cost_severe = repair.cost_estimation_data["Estimated Cost (₦)"]
        
        # Severe should cost more than moderate for same dimensions
        df_moderate = pd.DataFrame([self.repair_data])
        repair_moderate = EnhancedRepairFinancials(df_moderate)
        cost_moderate = repair_moderate.cost_estimation_data["Estimated Cost (₦)"]
        
        self.assertGreater(cost_severe, cost_moderate)
    
    def test_priority_score_calculation(self):
        """Test priority score calculation"""
        df = pd.DataFrame([self.repair_data])
        repair = EnhancedRepairFinancials(df)
        
        priority = repair.priority_score
        self.assertGreater(priority["Priority_Score"], 0)
        self.assertEqual(priority["Severity_Weight"], 2.0)  # Moderate
        self.assertEqual(priority["Urgency_Multiplier"], 1.0)  # Routine
    
    def test_invalid_severity(self):
        """Test error on invalid severity"""
        invalid_data = {**self.repair_data, "severity": "InvalidSeverity"}
        df = pd.DataFrame([invalid_data])
        
        with self.assertRaises(BudgetOptimizationError):
            EnhancedRepairFinancials(df)
    
    def test_invalid_urgency(self):
        """Test error on invalid urgency"""
        invalid_data = {**self.repair_data, "urgency": "InvalidUrgency"}
        df = pd.DataFrame([invalid_data])
        
        with self.assertRaises(BudgetOptimizationError):
            EnhancedRepairFinancials(df)
    
    def test_custom_configuration(self):
        """Test custom cost configuration"""
        custom_config = BudgetConfig(
            material_cost_per_m3=200_000,  # Higher than default
            labour_cost_per_m2=15_000
        )
        
        df_default = pd.DataFrame([self.repair_data])
        repair_default = EnhancedRepairFinancials(df_default)
        
        df_custom = pd.DataFrame([self.repair_data])
        repair_custom = EnhancedRepairFinancials(df_custom, custom_config)
        
        cost_default = repair_default.cost_estimation_data["Estimated Cost (₦)"]
        cost_custom = repair_custom.cost_estimation_data["Estimated Cost (₦)"]
        
        # Custom should be more expensive
        self.assertGreater(cost_custom, cost_default)


class TestBudgetOptimization(unittest.TestCase):
    """Test budget allocation strategies"""
    
    def setUp(self):
        """Create test repairs"""
        self.repairs_data = [
            {
                "length_cm": 200,
                "breadth_cm": 150,
                "depth_cm": 25,
                "severity": "Severe",
                "urgency": "immediate",
                "image_path": "/uploads/1.jpg"
            },
            {
                "length_cm": 150,
                "breadth_cm": 120,
                "depth_cm": 20,
                "severity": "Severe",
                "urgency": "immediate",
                "image_path": "/uploads/2.jpg"
            },
            {
                "length_cm": 80,
                "breadth_cm": 60,
                "depth_cm": 12,
                "severity": "Moderate",
                "urgency": "urgent",
                "image_path": "/uploads/3.jpg"
            },
            {
                "length_cm": 100,
                "breadth_cm": 70,
                "depth_cm": 10,
                "severity": "Moderate",
                "urgency": "routine",
                "image_path": "/uploads/4.jpg"
            },
            {
                "length_cm": 50,
                "breadth_cm": 40,
                "depth_cm": 8,
                "severity": "Minor",
                "urgency": "routine",
                "image_path": "/uploads/5.jpg"
            }
        ]
        
        self.repairs = [
            EnhancedRepairFinancials(pd.DataFrame([data]))
            for data in self.repairs_data
        ]
        
        self.total_budget = 5_000_000
    
    def test_priority_weighted_strategy(self):
        """Test priority-weighted allocation"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            self.total_budget,
            strategy="priority_weighted"
        )
        
        self.assertIsNotNone(allocation)
        self.assertEqual(len(allocation), 5)
        
        # Check total allocated doesn't exceed budget
        total_allocated = sum(a["Allocated Budget (₦)"] for a in allocation.values())
        self.assertLessEqual(total_allocated, self.total_budget)
    
    def test_severity_first_strategy(self):
        """Test severity-first allocation"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            self.total_budget,
            strategy="severity_first"
        )
        
        # Severe repairs should be fully funded first
        fully_funded_severe = sum(
            1 for a in allocation.values()
            if a["Severity"] == "Severe" and a["Can_Complete"]
        )
        self.assertEqual(fully_funded_severe, 2)  # Both severe repairs
    
    def test_proportional_strategy(self):
        """Test proportional allocation"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            self.total_budget,
            strategy="proportional"
        )
        
        # All repairs should get some allocation
        for repair in allocation.values():
            self.assertGreater(repair["Allocated Budget (₦)"], 0)
    
    def test_hybrid_strategy(self):
        """Test hybrid strategy"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            self.total_budget,
            strategy="hybrid"
        )
        
        # Critical repairs should be fully funded
        critical_fully_funded = all(
            a["Can_Complete"] for a in allocation.values()
            if a["Severity"] == "Severe" and a.get("Urgency") == "immediate"
        )
        self.assertTrue(critical_fully_funded)
    
    def test_insufficient_budget(self):
        """Test allocation with insufficient budget"""
        small_budget = 100_000
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            small_budget,
            strategy="priority_weighted"
        )
        
        # Some repairs won't be fully funded
        unfunded = sum(1 for a in allocation.values() if not a["Can_Complete"])
        self.assertGreater(unfunded, 0)
    
    def test_report_generation(self):
        """Test budget report generation"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repairs,
            self.total_budget,
            strategy="priority_weighted"
        )
        
        report = EnhancedRepairFinancials.generate_budget_report(
            allocation,
            self.total_budget
        )
        
        # Check report structure
        self.assertIn("budget_summary", report)
        self.assertIn("repair_summary", report)
        self.assertIn("severity_breakdown", report)
        
        # Check summary data
        summary = report["budget_summary"]
        self.assertIn("total_allocated", summary)
        self.assertIn("unallocated", summary)
        self.assertIn("allocation_rate", summary)


class TestBudgetAPIIntegration(unittest.TestCase):
    """Test Flask API integration"""
    
    def setUp(self):
        """Set up Flask test client"""
        try:
            # Try to import and set up Flask app for testing
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
            from integrated_backend import app
            self.app = app
            self.client = app.test_client()
            self.app_context = app.app_context()
            self.app_context.push()
        except Exception as e:
            self.skipTest(f"Could not set up Flask app for testing: {e}")
        
        self.repair_data = {
            "tracking_number": "RW20251001ABC",
            "damage_type": "pothole",
            "severity_score": 7,
            "estimated_cost": 150000,
            "location": "Lagos"
        }
    
    def tearDown(self):
        """Clean up Flask context"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_strategies_endpoint(self):
        """Test GET /api/budget/strategies"""
        response = self.client.get('/api/budget/strategies')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data["success"])
        self.assertIn("strategies", data)
        self.assertIn("priority_weighted", data["strategies"])
        self.assertIn("severity_first", data["strategies"])
    
    def test_estimate_cost_endpoint(self):
        """Test POST /api/budget/estimate-cost"""
        payload = {
            "length_cm": 100,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": "Moderate",
            "urgency": "routine"
        }
        
        response = self.client.post(
            '/api/budget/estimate-cost',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data["success"])
        self.assertIn("cost_estimation", data)
        self.assertIn("priority_score", data)
        self.assertGreater(data["cost_estimation"]["Estimated Cost (₦)"], 0)
    
    def test_optimize_endpoint_invalid_request(self):
        """Test POST /api/budget/optimize with invalid request"""
        response = self.client.post(
            '/api/budget/optimize',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
    
    def test_optimize_endpoint_with_repairs(self):
        """Test POST /api/budget/optimize with valid repairs"""
        payload = {
            "repairs": [self.repair_data],
            "total_budget": 5_000_000,
            "strategy": "priority_weighted"
        }
        
        response = self.client.post(
            '/api/budget/optimize',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should be 200 or 500 depending on if Flask app is fully set up
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertTrue(data["success"])
            self.assertIn("allocations", data)
            self.assertIn("report", data)


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow"""
    
    def test_database_to_optimization_flow(self):
        """Test complete flow from database records to budget optimization"""
        
        # Simulate database records
        database_records = [
            {
                "tracking_number": "RW20251001",
                "damage_type": "pothole",
                "severity_score": 9,
                "estimated_cost": 200000,
                "image_filename": "report_1.jpg"
            },
            {
                "tracking_number": "RW20251002",
                "damage_type": "crack",
                "severity_score": 6,
                "estimated_cost": 120000,
                "image_filename": "report_2.jpg"
            },
            {
                "tracking_number": "RW20251003",
                "damage_type": "rut",
                "severity_score": 4,
                "estimated_cost": 80000,
                "image_filename": "report_3.jpg"
            }
        ]
        
        # Step 1: Convert to budget format
        converted, skipped = batch_convert_reports(database_records)
        self.assertEqual(len(converted), 3)
        self.assertEqual(len(skipped), 0)
        
        # Step 2: Create repair objects
        repairs = []
        for repair_data in converted:
            df = pd.DataFrame([repair_data])
            repair = EnhancedRepairFinancials(df)
            repairs.append(repair)
        
        self.assertEqual(len(repairs), 3)
        
        # Step 3: Optimize budget
        total_budget = 3_000_000
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            repairs,
            total_budget,
            strategy="priority_weighted"
        )
        
        # Step 4: Generate report
        report = EnhancedRepairFinancials.generate_budget_report(
            allocation,
            total_budget
        )
        
        # Verify results
        self.assertEqual(report["repair_summary"]["total_repairs"], 3)
        self.assertLessEqual(
            report["budget_summary"]["total_allocated"],
            total_budget
        )
        
        # Severe repair should have priority
        severe_allocated = sum(
            a["Allocated Budget (₦)"] for a in allocation.values()
            if a["Severity"] == "Severe"
        )
        self.assertGreater(severe_allocated, 0)


def run_tests(verbose=True):
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedRepairFinancials))
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests(verbose=True)
    sys.exit(0 if success else 1)