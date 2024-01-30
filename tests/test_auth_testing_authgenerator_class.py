"""
Unit tests for the AuthGenerator class in the alexlib.auth module.

This test module provides a comprehensive suite of tests for ensuring the correct functionality of the AuthGenerator class, including instantiation, template generation, and the generation of Auth objects from templates.
"""

from unittest import TestCase, main
from pathlib import Path
from alexlib.auth import AuthGenerator, Auth
from tempfile import TemporaryDirectory

from alexlib.crypto import SecretValue


class TestAuthGeneratorInstantiation(TestCase):
    """
    Test cases for the instantiation of the AuthGenerator class and template file creation.
    """

    def setUp(self):
        """
        Set up a temporary directory for test files.
        """
        self.test_dir = TemporaryDirectory()

    def tearDown(self):
        """
        Clean up the temporary directory after tests.
        """
        self.test_dir.cleanup()

    def test_instantiation_and_template_creation(self):
        """
        Test whether the AuthGenerator correctly instantiates and creates a template file.
        """
        test_path = Path(self.test_dir.name, "test_template.json")
        AuthGenerator(name="test_template", path=test_path)
        self.assertTrue(test_path.exists(), "Template file was not created correctly.")


class TestAuthGeneratorTemplateGeneration(TestCase):
    """
    Test cases for verifying the correct generation of authentication templates by AuthGenerator.
    """

    def setUp(self):
        """
        Set up a temporary directory for test files.
        """
        self.test_dir = TemporaryDirectory()

    def tearDown(self):
        """
        Clean up the temporary directory after tests.
        """
        self.test_dir.cleanup()

    def test_template_generation(self):
        """
        Test if the authentication templates are generated correctly.
        """
        # Example test to check if templates are generated correctly
        # This test needs to be customized based on the actual implementation details
        locales = ["remote", "local"]
        envs = ["dev", "prod"]
        databases = ["postgres", "mysql"]
        generator = AuthGenerator(locales=locales, envs=envs, databases=databases)
        templates = generator.mk_all_templates()
        expected_keys = [
            "remote.dev.postgres",
            "remote.prod.postgres",
            "local.dev.postgres",
            "local.prod.postgres",
            "remote.dev.mysql",
            "remote.prod.mysql",
            "local.dev.mysql",
            "local.prod.mysql",
        ]
        self.assertListEqual(
            sorted(list(templates.keys())),
            sorted(expected_keys),
            "Generated templates keys do not match expected keys.",
        )


class TestAuthGeneratorGenerateMethod(TestCase):
    """
    Test cases for the `generate` method of the AuthGenerator class.
    """

    def setUp(self):
        """
        Set up a temporary directory for test files.
        """
        self.test_dir = TemporaryDirectory()
        self.test_path = Path(self.test_dir.name) / "test_template.json"

    def tearDown(self):
        """
        Clean up the temporary directory after tests.
        """
        self.test_dir.cleanup()

    def test_generate_method(self):
        """
        Test the `generate` method for creating Auth objects from templates.
        """
        # Example test to check the generate method
        # This test needs to be customized based on the actual implementation details
        generator = AuthGenerator(
            name="test_template",
            path=self.test_path,
            locales=["remote", "local"],
            envs=["dev", "prod"],
            databases=["postgres", "mysql"],
        )

        # Generate the templates
        templates = generator.mk_all_templates()
        # Generate the Auth objects
        auth_objects = {
            key: Auth.from_dict(key, template)
            for key, template in generator.generate(templates).items()
        }
        # Check if the Auth objects are generated correctly
        self.assertIsInstance(
            auth_objects, dict, "Auth objects are not generated correctly."
        )
        self.assertEqual(
            len(auth_objects), 8, "Auth objects are not generated correctly."
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.postgres"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.postgres"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.dev.mysql"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.dev.mysql"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.postgres"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.postgres"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["remote.prod.mysql"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"],
            Auth,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"].username,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"].password,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"].host,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"].port,
            SecretValue,
            "Auth objects are not generated correctly.",
        )
        self.assertIsInstance(
            auth_objects["local.prod.mysql"].database,
            SecretValue,
            "Auth objects are not generated correctly.",
        )


if __name__ == "__main__":
    main()
