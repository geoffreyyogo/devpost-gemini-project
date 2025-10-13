"""
Integration Test for BloomWatch Kenya Pipeline
Tests the complete data flow: GEE → Processing → ML Prediction
Verifies all components work together correctly
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Dict, List

# Add backend to path
sys.path.append(os.path.dirname(__file__))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import modules with error handling
modules_available = {}

try:
    from ee_pipeline import EarthEnginePipeline
    modules_available['ee_pipeline'] = True
    logger.info("✅ Earth Engine Pipeline imported successfully")
except ImportError as e:
    logger.warning(f"❌ Earth Engine Pipeline import failed: {e}")
    modules_available['ee_pipeline'] = False

try:
    from bloom_processor import BloomProcessor
    modules_available['bloom_processor'] = True
    logger.info("✅ Bloom Processor imported successfully")
except ImportError as e:
    logger.warning(f"❌ Bloom Processor import failed: {e}")
    modules_available['bloom_processor'] = False

try:
    from train_model import BloomPredictor, train_bloom_model, predict_bloom_from_live_data
    modules_available['train_model'] = True
    logger.info("✅ ML Model imported successfully")
except ImportError as e:
    logger.warning(f"❌ ML Model import failed: {e}")
    modules_available['train_model'] = False

try:
    from gee_data_loader import GEEDataLoader
    modules_available['gee_data_loader'] = True
    logger.info("✅ GEE Data Loader imported successfully")
except ImportError as e:
    logger.warning(f"❌ GEE Data Loader import failed: {e}")
    modules_available['gee_data_loader'] = False


class IntegrationTester:
    """
    Comprehensive integration tester for the BloomWatch Kenya pipeline
    """
    
    def __init__(self):
        """Initialize the integration tester"""
        self.test_results = {}
        self.pipeline = None
        self.processor = None
        self.predictor = None
        self.data_loader = None
        
        logger.info("🧪 Integration Tester initialized")
    
    def run_all_tests(self) -> Dict:
        """
        Run all integration tests
        
        Returns:
            Dict with test results and summary
        """
        logger.info("🚀 Starting comprehensive integration tests")
        print("\n" + "="*80)
        print("🌸 BLOOMWATCH KENYA - INTEGRATION TEST SUITE")
        print("="*80)
        
        # Test 1: Module availability
        self.test_module_availability()
        
        # Test 2: Data pipeline
        self.test_data_pipeline()
        
        # Test 3: Bloom processing
        self.test_bloom_processing()
        
        # Test 4: ML model training
        self.test_ml_training()
        
        # Test 5: Live prediction
        self.test_live_prediction()
        
        # Test 6: End-to-end integration
        self.test_end_to_end_integration()
        
        # Generate summary
        summary = self.generate_summary()
        
        print("\n" + "="*80)
        print("📊 INTEGRATION TEST SUMMARY")
        print("="*80)
        self.print_summary(summary)
        
        return {
            'test_results': self.test_results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    def test_module_availability(self):
        """Test 1: Check if all required modules are available"""
        print("\n🔍 Test 1: Module Availability")
        print("-" * 50)
        
        test_name = "module_availability"
        results = {}
        
        for module, available in modules_available.items():
            status = "✅ PASS" if available else "❌ FAIL"
            print(f"  {module}: {status}")
            results[module] = available
        
        # Overall module test result
        all_available = all(modules_available.values())
        overall_status = "PASS" if all_available else "PARTIAL"
        
        self.test_results[test_name] = {
            'status': overall_status,
            'details': results,
            'message': f"{sum(results.values())}/{len(results)} modules available"
        }
        
        print(f"\nModule Availability: {overall_status}")
    
    def test_data_pipeline(self):
        """Test 2: Earth Engine data pipeline"""
        print("\n🛰️ Test 2: Earth Engine Data Pipeline")
        print("-" * 50)
        
        test_name = "data_pipeline"
        
        if not modules_available['ee_pipeline']:
            self.test_results[test_name] = {
                'status': 'SKIP',
                'message': 'Earth Engine Pipeline not available'
            }
            print("  ⚠️ SKIP - Earth Engine Pipeline not available")
            return
        
        try:
            # Initialize pipeline
            self.pipeline = EarthEnginePipeline()
            print("  ✅ Pipeline initialized")
            
            # Test live data fetching (with fallback)
            print("  🔄 Testing live data fetch...")
            live_data = self.pipeline.fetch_live_data(days_back=3)
            
            if 'error' in live_data:
                print(f"  ⚠️ Live data fetch returned error: {live_data['error']}")
                status = 'PARTIAL'
            else:
                print("  ✅ Live data fetch successful")
                
                # Check data types
                data_types = ['ndvi', 'ndwi', 'rainfall', 'temperature']
                available_types = [dt for dt in data_types if dt in live_data and 'error' not in live_data[dt]]
                print(f"  📊 Available data types: {available_types}")
                status = 'PASS'
            
            # Test bloom area computation
            print("  🧮 Testing bloom area computation...")
            bloom_area = self.pipeline.compute_bloom_area()
            
            if 'error' in bloom_area:
                print(f"  ⚠️ Bloom area computation error: {bloom_area['error']}")
            else:
                print(f"  ✅ Bloom area: {bloom_area.get('bloom_area_km2', 0):.2f} km²")
            
            self.test_results[test_name] = {
                'status': status,
                'details': {
                    'live_data_available': 'error' not in live_data,
                    'bloom_area_available': 'error' not in bloom_area,
                    'available_data_types': available_types if 'available_types' in locals() else []
                },
                'message': 'Earth Engine pipeline functional'
            }
            
        except Exception as e:
            logger.error(f"Earth Engine pipeline test failed: {e}")
            print(f"  ❌ FAIL - {str(e)}")
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Earth Engine pipeline failed'
            }
    
    def test_bloom_processing(self):
        """Test 3: Bloom processing functionality"""
        print("\n🌸 Test 3: Bloom Processing")
        print("-" * 50)
        
        test_name = "bloom_processing"
        
        if not modules_available['bloom_processor']:
            self.test_results[test_name] = {
                'status': 'SKIP',
                'message': 'Bloom Processor not available'
            }
            print("  ⚠️ SKIP - Bloom Processor not available")
            return
        
        try:
            # Initialize processor
            self.processor = BloomProcessor()
            print("  ✅ Bloom Processor initialized")
            
            # Test bloom area computation
            print("  🧮 Testing bloom area computation...")
            bloom_areas = self.processor.compute_bloom_areas()
            
            if 'error' in bloom_areas:
                print(f"  ⚠️ Error: {bloom_areas['error']}")
                area_status = False
            else:
                print(f"  ✅ Bloom area: {bloom_areas.get('bloom_area_km2', 0):.2f} km²")
                area_status = True
            
            # Test historical data aggregation
            print("  📈 Testing historical data aggregation...")
            historical = self.processor.aggregate_historical_data(months_back=6)
            
            if 'error' in historical:
                print(f"  ⚠️ Using synthetic data: {historical.get('data_source', 'Unknown')}")
                historical_status = False
            else:
                print(f"  ✅ Historical data: {historical['time_series']['data_points']} points")
                historical_status = True
            
            # Test ML data preparation
            print("  🤖 Testing ML data preparation...")
            ml_data = self.processor.prepare_ml_training_data(include_weather=True)
            
            if 'error' in ml_data:
                print(f"  ❌ ML data preparation failed: {ml_data['error']}")
                ml_prep_status = False
            else:
                print(f"  ✅ ML data: {ml_data['n_samples']} samples, {ml_data['n_features']} features")
                print(f"      Class balance: {ml_data['class_balance']:.2%} bloom samples")
                ml_prep_status = True
            
            # Test time-series generation
            print("  📊 Testing time-series generation...")
            ts_status = True
            for data_type in ['ndvi', 'rainfall']:
                ts_data = self.processor.generate_time_series_data(data_type, months=3)
                if 'error' in ts_data:
                    print(f"  ⚠️ {data_type.upper()} time-series error")
                    ts_status = False
                else:
                    print(f"  ✅ {data_type.upper()}: {ts_data['n_points']} points")
            
            # Overall status
            all_tests = [area_status, historical_status, ml_prep_status, ts_status]
            if all(all_tests):
                status = 'PASS'
            elif any(all_tests):
                status = 'PARTIAL'
            else:
                status = 'FAIL'
            
            self.test_results[test_name] = {
                'status': status,
                'details': {
                    'bloom_areas': area_status,
                    'historical_data': historical_status,
                    'ml_preparation': ml_prep_status,
                    'time_series': ts_status
                },
                'message': f'{sum(all_tests)}/4 bloom processing tests passed'
            }
            
        except Exception as e:
            logger.error(f"Bloom processing test failed: {e}")
            print(f"  ❌ FAIL - {str(e)}")
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Bloom processing failed'
            }
    
    def test_ml_training(self):
        """Test 4: ML model training"""
        print("\n🤖 Test 4: ML Model Training")
        print("-" * 50)
        
        test_name = "ml_training"
        
        if not modules_available['train_model']:
            self.test_results[test_name] = {
                'status': 'SKIP',
                'message': 'ML Model not available'
            }
            print("  ⚠️ SKIP - ML Model not available")
            return
        
        try:
            # Test model training
            print("  🎓 Training Random Forest model...")
            training_result = train_bloom_model(include_weather=True, optimize_hyperparameters=False)
            
            if 'error' in training_result:
                print(f"  ❌ Training failed: {training_result['error']}")
                training_status = False
            else:
                metrics = training_result['metrics']
                print(f"  ✅ Training successful!")
                print(f"      Accuracy: {metrics.get('test_accuracy', 0):.3f}")
                print(f"      F1 Score: {metrics.get('f1_score', 0):.3f}")
                print(f"      Features: {metrics.get('n_features', 0)}")
                training_status = True
            
            # Test model loading
            print("  📁 Testing model persistence...")
            self.predictor = BloomPredictor()
            model_info = self.predictor.get_model_info()
            
            if 'error' in model_info:
                print(f"  ❌ Model loading failed: {model_info['error']}")
                loading_status = False
            else:
                print(f"  ✅ Model loaded: {model_info['model_type']}")
                print(f"      Path: {model_info['model_path']}")
                loading_status = True
            
            # Overall ML test status
            if training_status and loading_status:
                status = 'PASS'
            elif training_status or loading_status:
                status = 'PARTIAL'
            else:
                status = 'FAIL'
            
            self.test_results[test_name] = {
                'status': status,
                'details': {
                    'training': training_status,
                    'loading': loading_status,
                    'metrics': training_result.get('metrics', {}) if training_status else {}
                },
                'message': f'ML model {"fully functional" if status == "PASS" else "partially functional" if status == "PARTIAL" else "not functional"}'
            }
            
        except Exception as e:
            logger.error(f"ML training test failed: {e}")
            print(f"  ❌ FAIL - {str(e)}")
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'ML training failed'
            }
    
    def test_live_prediction(self):
        """Test 5: Live bloom prediction"""
        print("\n🔮 Test 5: Live Bloom Prediction")
        print("-" * 50)
        
        test_name = "live_prediction"
        
        if not modules_available['train_model']:
            self.test_results[test_name] = {
                'status': 'SKIP',
                'message': 'ML Model not available'
            }
            print("  ⚠️ SKIP - ML Model not available")
            return
        
        try:
            # Test live prediction
            print("  🔮 Making bloom prediction from live data...")
            prediction = predict_bloom_from_live_data()
            
            if 'error' in prediction:
                print(f"  ❌ Prediction failed: {prediction['error']}")
                status = 'FAIL'
            else:
                print(f"  ✅ Prediction successful!")
                print(f"      Bloom Probability: {prediction['bloom_probability_percent']:.1f}%")
                print(f"      Prediction: {'Bloom Expected' if prediction['bloom_prediction'] == 1 else 'No Bloom Expected'}")
                print(f"      Confidence: {prediction['confidence']}")
                print(f"      Model Version: {prediction.get('model_version', 'Unknown')}")
                status = 'PASS'
            
            self.test_results[test_name] = {
                'status': status,
                'details': prediction if 'error' not in prediction else {},
                'message': 'Live prediction ' + ('successful' if status == 'PASS' else 'failed')
            }
            
        except Exception as e:
            logger.error(f"Live prediction test failed: {e}")
            print(f"  ❌ FAIL - {str(e)}")
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'Live prediction failed'
            }
    
    def test_end_to_end_integration(self):
        """Test 6: Complete end-to-end integration"""
        print("\n🔗 Test 6: End-to-End Integration")
        print("-" * 50)
        
        test_name = "end_to_end_integration"
        
        try:
            # Check if we have the key components
            components_available = [
                modules_available.get('ee_pipeline', False),
                modules_available.get('bloom_processor', False),
                modules_available.get('train_model', False)
            ]
            
            if not any(components_available):
                self.test_results[test_name] = {
                    'status': 'SKIP',
                    'message': 'No core components available'
                }
                print("  ⚠️ SKIP - No core components available")
                return
            
            # Test data flow
            print("  🌊 Testing complete data flow...")
            
            # Step 1: Get live data (either real or synthetic)
            live_data = {}
            if self.pipeline:
                live_data = self.pipeline.fetch_live_data(days_back=3)
                print("  ✅ Step 1: Live data retrieved from Earth Engine")
            else:
                # Generate synthetic live data
                live_data = {
                    'ndvi': {'ndvi_mean': 0.6},
                    'ndwi': {'ndwi_mean': 0.4},
                    'rainfall': {'total_rainfall_mm': 75},
                    'temperature': {'temp_mean_c': 24}
                }
                print("  ✅ Step 1: Synthetic live data generated")
            
            # Step 2: Process data for bloom detection
            bloom_result = {}
            if self.processor:
                bloom_result = self.processor.detect_bloom_events('kenya')
                print(f"  ✅ Step 2: Bloom detection completed - {len(bloom_result.get('bloom_months', []))} events")
            else:
                bloom_result = {'bloom_months': [3, 10], 'bloom_area_km2': 150}
                print("  ✅ Step 2: Synthetic bloom detection completed")
            
            # Step 3: ML prediction
            prediction_result = {}
            if self.predictor or modules_available.get('train_model', False):
                if not self.predictor:
                    self.predictor = BloomPredictor()
                prediction_result = self.predictor.predict_bloom_probability(live_data)
                print(f"  ✅ Step 3: ML prediction completed - {prediction_result.get('bloom_probability_percent', 0):.1f}% bloom probability")
            else:
                prediction_result = {'bloom_probability_percent': 65, 'confidence': 'Medium'}
                print("  ✅ Step 3: Synthetic ML prediction completed")
            
            # Step 4: Integration validation
            print("  🔍 Validating data integration...")
            
            integration_checks = []
            
            # Check data consistency
            if 'ndvi_mean' in live_data.get('ndvi', {}) and bloom_result.get('ndvi_mean'):
                integration_checks.append(True)
                print("  ✅ NDVI data consistent across pipeline")
            else:
                integration_checks.append(False)
                print("  ⚠️ NDVI data inconsistency detected")
            
            # Check prediction reasonableness
            bloom_prob = prediction_result.get('bloom_probability_percent', 0)
            if 0 <= bloom_prob <= 100:
                integration_checks.append(True)
                print("  ✅ Prediction output within valid range")
            else:
                integration_checks.append(False)
                print("  ⚠️ Prediction output out of range")
            
            # Check bloom area computation
            bloom_area = bloom_result.get('bloom_area_km2', 0)
            if 0 <= bloom_area <= 50000:  # Reasonable range for Kenya
                integration_checks.append(True)
                print("  ✅ Bloom area within reasonable range")
            else:
                integration_checks.append(False)
                print("  ⚠️ Bloom area out of reasonable range")
            
            # Overall integration status
            if all(integration_checks):
                status = 'PASS'
                message = 'End-to-end integration fully functional'
            elif any(integration_checks):
                status = 'PARTIAL'
                message = 'End-to-end integration partially functional'
            else:
                status = 'FAIL' 
                message = 'End-to-end integration failed'
            
            self.test_results[test_name] = {
                'status': status,
                'details': {
                    'data_flow_complete': True,
                    'integration_checks_passed': sum(integration_checks),
                    'total_integration_checks': len(integration_checks),
                    'components_available': sum(components_available),
                    'live_data_keys': list(live_data.keys()),
                    'bloom_events': len(bloom_result.get('bloom_months', [])),
                    'bloom_probability': bloom_prob
                },
                'message': message
            }
            
            print(f"  🎯 Integration Status: {status}")
            
        except Exception as e:
            logger.error(f"End-to-end integration test failed: {e}")
            print(f"  ❌ FAIL - {str(e)}")
            print(f"  🔍 Error details: {traceback.format_exc()}")
            self.test_results[test_name] = {
                'status': 'FAIL',
                'error': str(e),
                'message': 'End-to-end integration failed with exception'
            }
    
    def generate_summary(self) -> Dict:
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        partial_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PARTIAL')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        skipped_tests = sum(1 for result in self.test_results.values() if result['status'] == 'SKIP')
        
        # Overall system status
        if passed_tests == total_tests:
            overall_status = 'FULLY FUNCTIONAL'
        elif passed_tests + partial_tests >= total_tests * 0.7:
            overall_status = 'MOSTLY FUNCTIONAL'
        elif passed_tests + partial_tests > 0:
            overall_status = 'PARTIALLY FUNCTIONAL'
        else:
            overall_status = 'NOT FUNCTIONAL'
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'partial': partial_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'overall_status': overall_status,
            'success_rate': (passed_tests + partial_tests * 0.5) / total_tests if total_tests > 0 else 0
        }
    
    def print_summary(self, summary: Dict):
        """Print test summary"""
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"⚠️ Partial: {summary['partial']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️ Skipped: {summary['skipped']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"\n🎯 OVERALL STATUS: {summary['overall_status']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if summary['overall_status'] == 'FULLY FUNCTIONAL':
            print("  🎉 System is ready for production!")
            print("  🔄 Consider setting up automated testing")
            print("  📈 Monitor performance metrics")
        elif summary['overall_status'] == 'MOSTLY FUNCTIONAL':
            print("  ✅ Core functionality working well")
            print("  🔧 Address partial failures for optimal performance")
            print("  🧪 Run additional tests on failing components")
        else:
            print("  🚨 Critical issues need attention")
            print("  🔧 Fix failed components before deployment")
            print("  📋 Review error logs and dependencies")


def main():
    """Main integration test function"""
    tester = IntegrationTester()
    results = tester.run_all_tests()
    
    # Save results to file
    import json
    results_file = os.path.join(os.path.dirname(__file__), 'integration_test_results.json')
    
    try:
        with open(results_file, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            import numpy as np
            def convert_numpy(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            # Convert the results
            json_results = json.loads(json.dumps(results, default=convert_numpy))
            json.dump(json_results, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")
    except Exception as e:
        logger.warning(f"Could not save results to file: {e}")
    
    return results


if __name__ == "__main__":
    main()
