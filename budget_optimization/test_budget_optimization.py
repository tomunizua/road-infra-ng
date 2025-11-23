"""Comprehensive Test Suite for Budget Optimization Module"""
import unittest
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.enhanced_budget import (
    EnhancedRepairFinancials,
    BudgetConfig,
    BudgetOptimizationError,
    demonstrate_optimization_strategies
)


class TestBudgetConfig(unittest.TestCase):
    """Test BudgetConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = BudgetConfig()
        self.assertEqual(config.material_cost_per_m3, 150_000)
        self.assertEqual(config.labour_cost_per_m2, 10_000)
        self.assertEqual(config.mobilization, 20_000)
        self.assertIn("Severe", config.severity_weights)
        self.assertIn("immediate", config.urgency_multipliers)
    
    def test_custom_config(self):
        """Test custom configuration"""
        custom_weights = {"Severe": 4.0, "Moderate": 2.0, "Minor": 1.0}
        config = BudgetConfig(severity_weights=custom_weights)
        self.assertEqual(config.severity_weights["Severe"], 4.0)
    
    def test_area_calculation_mode(self):
        """Test area calculation mode setting"""
        config = BudgetConfig(area_calculation_mode="elliptical")
        self.assertEqual(config.area_calculation_mode, "elliptical")


class TestEnhancedRepairFinancials(unittest.TestCase):
    """Test EnhancedRepairFinancials class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_repair = {
            "length_cm": 100,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": "Moderate",
            "image_path": "/path/to/image.jpg",
            "urgency": "routine"
        }
    
    def test_valid_repair_creation(self):
        """Test creating a valid repair object"""
        df = pd.DataFrame([self.sample_repair])
        repair = EnhancedRepairFinancials(df)
        
        self.assertEqual(repair.severity, "Moderate")
        self.assertEqual(repair.length, 100)
        self.assertIn("Estimated Cost (₦)", repair.cost_estimation_data)
        self.assertIn("Priority_Score", repair.priority_score)
    
    def test_missing_required_columns(self):
        """Test error handling for missing columns"""
        incomplete_repair = {
            "length_cm": 100,
            "breadth_cm": 80,
            # missing depth_cm
            "severity": "Moderate",
            "image_path": "/path/to/image.jpg"
        }
        
        df = pd.DataFrame([incomplete_repair])
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials(df)
        
        self.assertIn("Missing required columns", str(context.exception))
    
    def test_invalid_severity(self):
        """Test error handling for invalid severity"""
        invalid_repair = self.sample_repair.copy()
        invalid_repair["severity"] = "InvalidSeverity"
        
        df = pd.DataFrame([invalid_repair])
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials(df)
        
        self.assertIn("Invalid severity", str(context.exception))
    
    def test_invalid_urgency(self):
        """Test error handling for invalid urgency"""
        invalid_repair = self.sample_repair.copy()
        invalid_repair["urgency"] = "invalid_urgency"
        
        df = pd.DataFrame([invalid_repair])
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials(df)
        
        self.assertIn("Invalid urgency", str(context.exception))
    
    def test_negative_dimensions(self):
        """Test error handling for negative dimensions"""
        invalid_repair = self.sample_repair.copy()
        invalid_repair["length_cm"] = -100
        
        df = pd.DataFrame([invalid_repair])
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials(df)
        
        self.assertIn("positive values", str(context.exception))
    
    def test_cost_calculation_rectangular(self):
        """Test cost calculation with rectangular area"""
        config = BudgetConfig(area_calculation_mode="rectangular")
        df = pd.DataFrame([self.sample_repair])
        repair = EnhancedRepairFinancials(df, config)
        
        # Check cost is calculated
        cost = repair.cost_estimation_data["Estimated Cost (₦)"]
        self.assertGreater(cost, 0)
        self.assertEqual(isinstance(cost, int), True)
    
    def test_cost_calculation_elliptical(self):
        """Test cost calculation with elliptical area"""
        config = BudgetConfig(area_calculation_mode="elliptical")
        df = pd.DataFrame([self.sample_repair])
        repair = EnhancedRepairFinancials(df, config)
        
        # Elliptical should result in different (smaller) area
        cost = repair.cost_estimation_data["Estimated Cost (₦)"]
        self.assertGreater(cost, 0)
    
    def test_severity_multipliers(self):
        """Test that severity affects cost correctly"""
        costs = {}
        
        for severity in ["Minor", "Moderate", "Severe"]:
            repair_data = self.sample_repair.copy()
            repair_data["severity"] = severity
            df = pd.DataFrame([repair_data])
            repair = EnhancedRepairFinancials(df)
            costs[severity] = repair.cost_estimation_data["Estimated Cost (₦)"]
        
        # Severe should cost more than Moderate which should cost more than Minor
        self.assertGreater(costs["Moderate"], costs["Minor"])
        self.assertGreater(costs["Severe"], costs["Moderate"])
    
    def test_urgency_multipliers(self):
        """Test that urgency affects cost correctly"""
        costs = {}
        
        for urgency in ["routine", "urgent", "immediate"]:
            repair_data = self.sample_repair.copy()
            repair_data["urgency"] = urgency
            df = pd.DataFrame([repair_data])
            repair = EnhancedRepairFinancials(df)
            costs[urgency] = repair.cost_estimation_data["Estimated Cost (₦)"]
        
        # Immediate should cost more than urgent which should cost more than routine
        self.assertGreater(costs["urgent"], costs["routine"])
        self.assertGreater(costs["immediate"], costs["urgent"])
    
    def test_priority_score_calculation(self):
        """Test priority score is calculated"""
        df = pd.DataFrame([self.sample_repair])
        repair = EnhancedRepairFinancials(df)
        
        priority = repair.priority_score["Priority_Score"]
        self.assertGreater(priority, 0)
        self.assertIsInstance(priority, (int, float))
    
    def test_default_urgency(self):
        """Test default urgency is 'routine' when not provided"""
        repair_data = self.sample_repair.copy()
        del repair_data["urgency"]
        
        df = pd.DataFrame([repair_data])
        repair = EnhancedRepairFinancials(df)
        
        self.assertEqual(repair.urgency, "routine")


class TestBudgetAllocationStrategies(unittest.TestCase):
    """Test different budget allocation strategies"""
    
    def setUp(self):
        """Set up test fixtures with multiple repairs"""
        self.repairs_data = [
            {
                "length_cm": 100,
                "breadth_cm": 80,
                "depth_cm": 15,
                "severity": "Severe",
                "image_path": "/path/1.jpg",
                "urgency": "immediate"
            },
            {
                "length_cm": 60,
                "breadth_cm": 50,
                "depth_cm": 10,
                "severity": "Moderate",
                "image_path": "/path/2.jpg",
                "urgency": "urgent"
            },
            {
                "length_cm": 40,
                "breadth_cm": 35,
                "depth_cm": 5,
                "severity": "Minor",
                "image_path": "/path/3.jpg",
                "urgency": "routine"
            }
        ]
        
        self.repair_objects = []
        for repair_data in self.repairs_data:
            df = pd.DataFrame([repair_data])
            self.repair_objects.append(EnhancedRepairFinancials(df))
        
        self.total_budget = 5_000_000
    
    def test_priority_weighted_allocation(self):
        """Test priority-weighted allocation strategy"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repair_objects,
            self.total_budget,
            strategy="priority_weighted"
        )
        
        # Verify structure
        self.assertGreater(len(allocation), 0)
        
        for repair_key, repair_data in allocation.items():
            self.assertIn("Allocated Budget (₦)", repair_data)
            self.assertIn("Funding Ratio", repair_data)
            self.assertIn("Can_Complete", repair_data)
            self.assertGreaterEqual(repair_data["Allocated Budget (₦)"], 0)
        
        # Total allocated should not exceed budget
        total_allocated = sum(v["Allocated Budget (₦)"] for v in allocation.values())
        self.assertLessEqual(total_allocated, self.total_budget)
    
    def test_severity_first_allocation(self):
        """Test severity-first allocation strategy"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repair_objects,
            self.total_budget,
            strategy="severity_first"
        )
        
        # Verify Severe repairs are prioritized
        severe_repairs = [v for v in allocation.values() if v["Severity"] == "Severe"]
        moderate_repairs = [v for v in allocation.values() if v["Severity"] == "Moderate"]
        
        if severe_repairs and moderate_repairs:
            # Severe should have better funding ratio
            avg_severe_ratio = sum(r["Funding Ratio"] for r in severe_repairs) / len(severe_repairs)
            avg_moderate_ratio = sum(r["Funding Ratio"] for r in moderate_repairs) / len(moderate_repairs)
            self.assertGreaterEqual(avg_severe_ratio, avg_moderate_ratio)
    
    def test_proportional_allocation(self):
        """Test proportional allocation strategy"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repair_objects,
            self.total_budget,
            strategy="proportional"
        )
        
        # Verify allocations are proportional to costs
        total_allocated = sum(v["Allocated Budget (₦)"] for v in allocation.values())
        self.assertLessEqual(total_allocated, self.total_budget)
        self.assertGreater(total_allocated, 0)
    
    def test_hybrid_allocation(self):
        """Test hybrid allocation strategy"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repair_objects,
            self.total_budget,
            strategy="hybrid"
        )
        
        # Verify structure
        self.assertGreater(len(allocation), 0)
        
        # Check if critical repairs exist and are fully funded
        critical = [v for v in allocation.values() if v.get("Category") == "Critical"]
        for repair in critical:
            self.assertTrue(repair["Can_Complete"])
            self.assertEqual(repair["Funding Ratio"], 1.0)
    
    def test_invalid_strategy(self):
        """Test error handling for invalid strategy"""
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials.optimize_budget_with_priorities(
                self.repair_objects,
                self.total_budget,
                strategy="invalid_strategy"
            )
        
        self.assertIn("Unknown strategy", str(context.exception))
    
    def test_empty_repairs_list(self):
        """Test error handling for empty repairs list"""
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials.optimize_budget_with_priorities(
                [],
                self.total_budget
            )
        
        self.assertIn("No repair objects", str(context.exception))
    
    def test_zero_budget(self):
        """Test error handling for zero budget"""
        with self.assertRaises(BudgetOptimizationError) as context:
            EnhancedRepairFinancials.optimize_budget_with_priorities(
                self.repair_objects,
                0
            )
        
        self.assertIn("positive", str(context.exception))
    
    def test_budget_report_generation(self):
        """Test budget report generation"""
        allocation = EnhancedRepairFinancials.optimize_budget_with_priorities(
            self.repair_objects,
            self.total_budget,
            strategy="priority_weighted"
        )
        
        report = EnhancedRepairFinancials.generate_budget_report(allocation, self.total_budget)
        
        # Verify report structure
        self.assertIn("budget_summary", report)
        self.assertIn("repair_summary", report)
        self.assertIn("severity_breakdown", report)
        
        # Verify values
        budget_summary = report["budget_summary"]
        self.assertEqual(budget_summary["total_budget"], self.total_budget)
        self.assertGreaterEqual(budget_summary["allocation_rate"], 0)
        self.assertLessEqual(budget_summary["allocation_rate"], 100)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests with realistic scenarios"""
    
    def test_real_world_scenario(self):
        """Test with realistic road damage data"""
        repairs = [
            {
                "length_cm": 150,
                "breadth_cm": 120,
                "depth_cm": 25,
                "severity": "Severe",
                "image_path": "/uploads/severe_pothole.jpg",
                "urgency": "immediate"
            },
            {
                "length_cm": 200,
                "breadth_cm": 150,
                "depth_cm": 20,
                "severity": "Severe",
                "image_path": "/uploads/severe_crack.jpg",
                "urgency": "immediate"
            },
            {
                "length_cm": 80,
                "breadth_cm": 60,
                "depth_cm": 12,
                "severity": "Moderate",
                "image_path": "/uploads/moderate_damage.jpg",
                "urgency": "urgent"
            },
            {
                "length_cm": 50,
                "breadth_cm": 40,
                "depth_cm": 8,
                "severity": "Minor",
                "image_path": "/uploads/minor_crack.jpg",
                "urgency": "routine"
            }
        ]
        
        results = demonstrate_optimization_strategies(repairs, budget=5_000_000)
        
        # Verify all strategies returned results
        self.assertEqual(len(results), 4)
        
        # Verify no errors occurred
        for strategy, result in results.items():
            self.assertNotIn("error", result, f"Strategy {strategy} returned error")
            self.assertIn("allocation", result)
            self.assertIn("report", result)
    
    def test_insufficient_budget_scenario(self):
        """Test scenario with insufficient budget"""
        repairs = [
            {
                "length_cm": 200,
                "breadth_cm": 150,
                "depth_cm": 25,
                "severity": "Severe",
                "image_path": "/uploads/1.jpg",
                "urgency": "immediate"
            },
            {
                "length_cm": 180,
                "breadth_cm": 140,
                "depth_cm": 22,
                "severity": "Severe",
                "image_path": "/uploads/2.jpg",
                "urgency": "immediate"
            }
        ]
        
        # Very small budget
        results = demonstrate_optimization_strategies(repairs, budget=200_000)
        
        # Hybrid should fail due to insufficient budget for critical repairs
        if "hybrid" in results:
            self.assertIn("error", results["hybrid"])
    
    def test_large_scale_scenario(self):
        """Test with large number of repairs"""
        repairs = []
        for i in range(50):
            severity = ["Severe", "Moderate", "Minor"][i % 3]
            urgency = ["immediate", "urgent", "routine"][i % 3]
            
            repairs.append({
                "length_cm": 50 + (i * 2),
                "breadth_cm": 40 + (i * 1.5),
                "depth_cm": 8 + (i % 5),
                "severity": severity,
                "image_path": f"/uploads/damage_{i}.jpg",
                "urgency": urgency
            })
        
        results = demonstrate_optimization_strategies(repairs, budget=50_000_000)
        
        # Verify all strategies completed
        for strategy in ["priority_weighted", "severity_first", "proportional"]:
            self.assertIn(strategy, results)
            self.assertNotIn("error", results[strategy])


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_null_values_in_dataframe(self):
        """Test handling of null values"""
        repair_data = {
            "length_cm": None,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": "Moderate",
            "image_path": "/path/to/image.jpg"
        }
        
        df = pd.DataFrame([repair_data])
        with self.assertRaises(BudgetOptimizationError):
            EnhancedRepairFinancials(df)
    
    def test_zero_dimensions(self):
        """Test handling of zero dimensions"""
        repair_data = {
            "length_cm": 0,
            "breadth_cm": 80,
            "depth_cm": 15,
            "severity": "Moderate",
            "image_path": "/path/to/image.jpg"
        }
        
        df = pd.DataFrame([repair_data])
        with self.assertRaises(BudgetOptimizationError):
            EnhancedRepairFinancials(df)
    
    def test_very_large_repairs(self):
        """Test handling of very large repair dimensions"""
        repair_data = {
            "length_cm": 10000,
            "breadth_cm": 8000,
            "depth_cm": 100,
            "severity": "Severe",
            "image_path": "/path/to/image.jpg"
        }
        
        df = pd.DataFrame([repair_data])
        repair = EnhancedRepairFinancials(df)
        
        # Should handle large values without error
        cost = repair.cost_estimation_data["Estimated Cost (₦)"]
        self.assertGreater(cost, 0)
        self.assertTrue(isinstance(cost, int))


def run_tests_with_report():
    """Run all tests and print detailed report"""
    print("\n" + "="*70)
    print("🧪 BUDGET OPTIMIZATION TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedRepairFinancials))
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetAllocationStrategies))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests_with_report()
    sys.exit(0 if success else 1)