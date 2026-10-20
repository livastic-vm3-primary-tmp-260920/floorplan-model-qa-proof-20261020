from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SyntheticVisualPageTests(unittest.TestCase):
 def test_static_page_no_external_dependencies(self):
  page=(ROOT/"docs/index.html").read_text()
  for tag in ('<script', '<iframe', 'fetch(', 'google-analytics', 'fonts.googleapis'):
   self.assertNotIn(tag,page)
  self.assertIn('fully invented exercise',page)
 def test_all_five_reported_classes_visible(self):
  html=(ROOT/"docs/index.html").read_text()
  for label in ('East wall','Entry door','North window','Cabinet','Bedroom'):
   self.assertIn(label,html)
if __name__=="__main__":unittest.main()
