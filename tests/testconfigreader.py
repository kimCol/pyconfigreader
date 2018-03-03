#! /usr/bin/env python

import os
import unittest2 as unittest
from pyconfigreader import ConfigReader
from pyconfigreader.exceptions import ThresholdError, ModeError
from uuid import uuid4
from testfixtures import TempDirectory

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    FileNotFoundError = FileNotFoundError
except NameError:
    FileNotFoundError = OSError


class TestConfigReaderTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = TempDirectory()
        self.file_path = os.path.join(self.tempdir.path, '{}.ini'.format(str(uuid4())))
        self.filename = os.path.basename(self.file_path)
        self.test_dir = self.tempdir.makedir('test_path')
        self.config_file = 'settings.ini'

    def tearDown(self):
        self.tempdir.cleanup()

    def test_returns_false_if_filename_not_absolute(self):
        with self.subTest(0):
            config = ConfigReader(self.file_path)
            self.assertTrue(os.path.isabs(config.filename))

        with self.subTest(1):
            config = ConfigReader()
            self.assertTrue(os.path.isabs(config.filename))

        with self.subTest(2):
            filename = os.path.join(
                os.path.expanduser('~'), 'settings.ini')
            config = ConfigReader()
            self.assertEqual(filename, config.filename)

        config.close()

        try:
            os.remove(config.filename)
        except FileNotFoundError:
            pass

    def test_returns_false_if_default_name_not_match(self):
        self.config = ConfigReader(self.file_path)
        expected = self.file_path
        self.assertEqual(self.config.filename, expected)
        self.config.close()

    def test_returns_false_if_name_not_changed(self):
        self.config = ConfigReader(self.file_path)
        path = os.path.join(self.test_dir, 'abc.ini')
        self.config.filename = path
        expected = path
        self.assertEqual(self.config.filename, expected)
        self.config.close()

    def test_returns_false_if_config_file_not_exists(self):
        self.config = ConfigReader(self.file_path)
        self.assertFalse(os.path.isfile(self.config.filename))
        self.config.close()

    def test_returns_false_if_config_file_exists(self):
        self.config = ConfigReader(self.file_path)
        self.config.to_file()
        self.assertTrue(os.path.isfile(self.config.filename))
        self.config.close()
        os.remove(self.config.filename)

    def test_returns_false_if_sections_not_exists(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('Sample', 'Example', 'MainSection')
        self.config.set('Sample', 'Example', 'OtherSection')
        expected = ['MainSection', 'OtherSection', 'main']
        self.assertListEqual(
            sorted(self.config.sections), sorted(expected))
        self.config.close()

    def test_returns_false_if_section_not_removed(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('Sample', 'Example', 'MainSection')
        self.config.set('Sample', 'Example', 'OtherSection')
        self.config.remove_section('main')
        expected = ['MainSection', 'OtherSection']
        self.assertListEqual(
            sorted(self.config.sections), sorted(expected))
        self.config.close()

    def test_returns_false_if_key_not_removed(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('Sample', 'Example', 'MainSection')
        self.config.set('Sample', 'Example', 'OtherSection')
        self.config.remove_option('Sample', 'MainSection')

        with self.subTest(0):
            self.assertIsNone(self.config.get(
                'Sample', section='MainSection'))

        with self.subTest(1):
            expected = ['MainSection', 'main', 'OtherSection']
            self.assertListEqual(sorted(
                self.config.sections), sorted(expected))
        self.config.close()

    def test_returns_false_if_dict_not_returned(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('Sample', 'Example', 'MainSection')
        self.config.set('Sample', 'Example', 'OtherSection')
        self.config.set('Name', 'File', 'OtherSection')
        self.assertIsInstance(
            self.config.show(output=False), dict)
        self.config.close()

    def test_returns_false_if_key_exists(self):
        self.config = ConfigReader(self.file_path)
        self.assertIsNone(self.config.get('Sample'))
        self.config.close()

    def test_returns_false_if_json_not_dumped(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('Sample', 'Example', 'MainSection')
        self.config.set('Sample', 'Example', 'OtherSection')
        self.config.set('name', 'File', 'OtherSection')
        self.config.remove_section('main')
        s_io = StringIO()
        self.config.to_json(s_io)
        s_io.seek(0)
        expected = s_io.read()

        self.assertEqual(self.config.to_json(), expected)
        self.config.close()

    def test_returns_false_if_json_file_not_created(self):
        self.config = ConfigReader(self.file_path)

        filename = os.path.join(self.test_dir, 'abc.json')
        with open(filename, 'w') as f:
            self.config.to_json(f)
        self.assertTrue(os.path.isfile(filename))
        self.config.close()

    def test_returns_false_if_defaults_are_changed(self):
        filename = os.path.join(
            os.path.expanduser('~'), '{}.cfg'.format(str(uuid4())))
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        dr = ConfigParser()
        dr.read(filename)
        dr.add_section('main')
        dr.add_section('MainSection')
        dr.set('main', 'new', 'False')
        dr.set('MainSection', 'browser', 'default')
        dr.set('MainSection', 'header', 'False')

        with open(filename, "w") as config_file:
            #dr.write(config_file)
            config_file.write('[main]\nnew = False\n')

        self.config = ConfigReader(filename)
        self.config.set('browser', 'default', 'MainSection')

        with self.subTest(0):
            result = self.config.get('new')
            self.assertFalse(result)

        with self.subTest(1):
            expected = 'default'
            self.assertEqual(
                self.config.get('browser', section='MainSection'), expected)

        with self.subTest(2):
            self.assertIsNone(self.config.get('browser'))

        with self.subTest(3):
            expected = 'Not set'
            self.assertEqual(
                self.config.get('default', default='Not set'), expected)

        self.config.close()
        os.remove(filename)

    def test_returns_false_if_environment_variables_not_set(self):
        self.config = ConfigReader(self.file_path)
        self.config.set('country', 'Kenya')
        self.config.set('continent', 'Africa')
        self.config.set('state', None)
        self.config.to_env()

        with self.subTest(0):
            self.assertEqual(os.environ['MAIN_COUNTRY'], 'Kenya')

        with self.subTest(1):
            self.assertEqual(os.environ['MAIN_CONTINENT'], 'Africa')

        with self.subTest(2):
            self.assertEqual(os.environ['MAIN_STATE'], 'None')
        self.config.close()

    def test_returns_false_if_section_prepend_failed(self):
        f = open('default.ini', 'w+')
        config = ConfigReader(self.file_path, f)
        config.set('country', 'Kenya')
        config.set('continent', 'Africa')
        config.set('state', None)
        config.set('count', '0', section='first')
        config.to_env()
        f.close()

        with self.subTest(0):
            self.assertEqual(os.environ.get('MAIN_COUNTRY'), 'Kenya')

        with self.subTest(1):
            self.assertEqual(os.environ.get('MAIN_CONTINENT'), 'Africa')

        with self.subTest(2):
            self.assertEqual(os.environ.get('MAIN_STATE'), 'None')

        with self.subTest(3):
            self.assertEqual(os.environ.get('FIRST_COUNT'), '0')

    def test_returns_false_if_value_not_evaluated(self):
        config = ConfigReader(self.file_path)
        config.set('truth', 'True')
        config.set('empty', '')
        config.set('count', '0', section='first')
        config.set('None', 'None', section='first')

        with self.subTest(0):
            self.assertTrue(config.get('truth'))

        with self.subTest(1):
            self.assertEqual(config.get('empty'), '')

        with self.subTest(2):
            self.assertIsNone(config.get('count'))

        with self.subTest(3):
            self.assertEqual(
                config.get('count', section='first'), 0)

        with self.subTest(4):
            self.assertIsNone(config.get('None'))
        config.close()

    def test_returns_false_if_exception_not_raised(self):
        config = ConfigReader(self.file_path)

        def edit_sections():
            config.sections = ['new_section']
        self.assertRaises(AttributeError, edit_sections)
        config.close()

    def test_returns_false_if_threshold_error_not_raised(self):
        config = ConfigReader(self.file_path)

        def do_search(threshold):
            config.search('read', threshold=threshold)

        with self.subTest(0):
            self.assertRaises(ThresholdError, do_search, 1.01)

        with self.subTest(1):
            self.assertRaises(ThresholdError, do_search, -1.0)
        config.close()

    def test_returns_false_if_match_not_found(self):
        config = ConfigReader(self.file_path)
        expected = ('reader', 'configreader', 'main')
        result = config.search('reader')
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_not_match_best(self):
        config = ConfigReader(self.file_path)
        config.set('header', 'confreader')

        expected = ('reader', 'configreader', 'main')
        result = config.search('confgreader')
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_exact_match_not_found(self):
        config = ConfigReader(self.file_path)
        config.set('title', 'The Place')

        expected = ('title', 'The Place', 'main')
        result = config.search('The Place', exact_match=True)
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_exact_match_found(self):
        config = ConfigReader(self.file_path)
        config.set('title', 'The Place')

        expected = ()
        result = config.search('The place', exact_match=True)
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_exact_match_not_found_case_insensitive(self):
        config = ConfigReader(self.file_path)
        config.set('title', 'The Place')

        expected = ('title', 'The Place', 'main')
        result = config.search('The place',
                               exact_match=True,
                               case_sensitive=False)
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_path_not_changed(self):
        f = open(self.file_path, 'w+')
        config = ConfigReader(file_object=f)
        new_path = os.path.join(
            os.path.expanduser('~'), '{}.ini'.format(str(uuid4()))
        )

        with self.subTest(0):
            self.assertFalse(os.path.isfile(new_path))

        config.filename = new_path

        with self.subTest(1):
            self.assertFalse(os.path.isfile(self.file_path))

        with self.subTest(2):
            self.assertFalse(os.path.isfile(new_path))

        config.to_file()

        with self.subTest(3):
            self.assertTrue(os.path.isfile(new_path))
        config.close()

    def test_returns_false_if_old_file_object_writable(self):
        f = open(self.file_path, 'w+')
        config = ConfigReader(file_object=f)
        new_path = os.path.join(
            os.path.expanduser('~'), '{}.ini'.format(str(uuid4()))
        )

        config.filename = new_path

        self.assertRaises(ValueError, lambda: f.write(''))
        config.close()

    def test_returns_false_if_contents_not_similar(self):
        f = open(self.file_path, 'w+')
        config = ConfigReader(file_object=f)
        new_path = os.path.join(
            os.path.expanduser('~'), '{}.ini'.format(str(uuid4()))
        )

        f.seek(0)
        expected = f.read()

        config.filename = new_path
        config.to_file()

        with open(new_path) as f2:
            result = f2.read()
        self.assertEqual(result, expected)
        config.close()

    def test_returns_false_if_file_object_cannot_update(self):
        f = open(self.file_path, 'w')

        self.assertRaises(ModeError, lambda: ConfigReader(file_object=f))
        f.close()

    def test_returns_false_if_contents_not_updated(self):
        f = open(self.file_path, 'w+')
        config = ConfigReader(file_object=f)
        config.set('name', 'first')

        with self.subTest(0):
            with open(self.file_path) as f2:
                result = f2.read()
            self.assertNotEqual(result, '')

        config.to_file()

        with self.subTest(1):
            with open(self.file_path) as f3:
                result = f3.read()
            self.assertNotEqual(result, '')
        f.close()

    def test_returns_false_if_file_object_and_filename_not_similar(self):
        with open(self.file_path, 'w+') as f:
            config = ConfigReader(file_object=f)
            self.assertEqual(config.filename, f.name)
            config.close()

    def test_returns_false_if_changes_not_written_to_file(self):
        config = ConfigReader(self.file_path)
        config.set('name', 'first')

        d = ConfigReader(self.file_path)
        with self.subTest(0):
            self.assertIsNone(d.get('name'))
        config.set('name', 'last', commit=True)
        config.close()

        d = ConfigReader(self.file_path)
        with self.subTest(1):
            self.assertEqual(d.get('name'), 'last')
        d.close()

    def test_returns_false_if_option_not_removed_from_file(self):
        config = ConfigReader(
            os.path.join(self.tempdir.path, '{}.ini'.format(str(uuid4()))))
        config.set('name', 'first', section='two')

        with self.subTest(0):
            self.assertEqual(config.get('name', section='two'), 'first')

        config.remove_key('name', section='two', commit=True)

        d = ConfigReader(self.file_path)
        with self.subTest(1):
            self.assertIsNone(d.get('name', section='two'))
        config.close()
        d.close()

    def test_returns_false_if_file_object_not_closed(self):
        config = ConfigReader(self.file_path)
        config.close()

        self.assertRaises(ValueError, lambda: config.set('first', 'false'))

    def test_returns_false_if_items_not_match(self):
        f_io = StringIO()
        config = ConfigReader(file_object=f_io)
        items = config.get_items('main')
        config.close()
        f_io.close()

        with self.subTest(0):
            self.assertIsInstance(items, dict)

        with self.subTest(1):
            self.assertEqual(items, {'reader': 'configreader'})

    def test_returns_false_if_object_not_context(self):
        with ConfigReader(self.file_path) as config:
            config.set('name', 'First', commit=True)
            name = config.get('name')

        self.assertEqual(name, 'First')


if __name__ == "__main__":
    unittest.main()
