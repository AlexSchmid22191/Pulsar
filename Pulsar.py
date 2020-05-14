from Interface import PulsarGUI
from Engine import Pulsarino
from pubsub.pub import addTopicDefnProvider, TOPIC_TREE_FROM_CLASS
import Topic_Tree
import wx


addTopicDefnProvider(Topic_Tree, TOPIC_TREE_FROM_CLASS)


def main():
    ex = wx.App()
    ex.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
    engine = Pulsarino()
    gui = PulsarGUI(parent=None)
    print('Engine initilized: {:s}'.format(str(engine.__class__)))
    print('GUI initialized: {:s}'.format(str(gui.__class__)))
    ex.MainLoop()


if __name__ == '__main__':
    main()
