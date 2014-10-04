import unittest
import test.accounts_tests
import test.transactions_tests
import test.payees_tests
import test.categories_tests
        
testsuite = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromModule(test.accounts_tests),
    unittest.TestLoader().loadTestsFromModule(test.transactions_tests),
    unittest.TestLoader().loadTestsFromModule(test.payees_tests),
    unittest.TestLoader().loadTestsFromModule(test.categories_tests)
    ])
unittest.TextTestRunner(verbosity=1).run(testsuite)