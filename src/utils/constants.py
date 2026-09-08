class Constants:
  def __init__(
    self,
    PPM: int = 50,
    FONT_SIZE: int = 20,
    SCREEN_WIDTH: int = 1280,
    SCREEN_HEIGHT: int = 720,
  ):
    self.PPM = PPM
    self.FONT_SIZE = FONT_SIZE
    self.SCREEN_WIDTH = SCREEN_WIDTH
    self.SCREEN_HEIGHT = SCREEN_HEIGHT

  def update_PPM(self, new_PPM: int):
    self.PPM = new_PPM
