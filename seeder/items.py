from seeder.model import Match

import scrapy

def item_subtype_from_model(classname, model):
  """
  Create a scrapy.Item subclass dynamically from a sqlalchmey model.
  """
  attr_names = {
    col.name: scrapy.Field()
    for col in model.__table__.columns
  }
  return type(classname, (scrapy.Item,), attr_names) 


MatchItem = item_subtype_from_model('MatchItem', Match)
