class Parser(object):

  def __init__(self, *args, **kwargs):
    pass

  def parse_items(self, response):
    raise NotImplementedError

  def parse_links(self, response):
    raise NotImplementedError
