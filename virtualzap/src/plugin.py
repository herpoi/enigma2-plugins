#
#  VirtualZap E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Coding idea and design by Vali
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
##################################################################################
#  
#  Modified by herpoi (herpoi2006@gmail.com)
#  https://github.com/herpoi
#
#  Picon finder and DirectoryBrowser from Extended NumberZap Plugin
#  Thanks to @vlamo <vlamodev@gmail.com>
#
##################################################################################
from time import localtime, time, strftime
from ServiceReference import ServiceReference
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigDirectory, getConfigListEntry, configfile, ConfigPosition, ConfigText, ConfigInteger
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap, MultiPixmap
from Components.FileList import FileList
from Components.ProgressBar import ProgressBar
from Components.SystemInfo import SystemInfo
from Components.ParentalControl import parentalControl
from Components.Sources.StaticText import StaticText
from Components.VideoWindow import VideoWindow
from Screens.Screen import Screen
from Screens.InfoBarGenerics import InfoBarShowHide, NumberZap, InfoBarPiP, InfoBarPlugins
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.EpgSelection import EPGSelection
from Screens.EventView import  EventViewEPGSelect
from Screens.PictureInPicture import PictureInPicture
from Plugins.Plugin import PluginDescriptor
from enigma import eServiceReference,  eTimer, getDesktop, ePixmap
from enigma import eServiceCenter, getBestPlayableServiceReference
from enigma import ePoint, eEPGCache
from skin import parseColor, loadSkin
from Tools.Directories import pathExists, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, SCOPE_CURRENT_PLUGIN, resolveFilename, getSize

InfoBarShowHideINIT = None

# for localized messages
from . import _

# PiPServiceRelation installed?
try:
	from Plugins.SystemPlugins.PiPServiceRelation.plugin import getRelationDict, CONFIG_FILE
	plugin_PiPServiceRelation_installed = True
except:
	plugin_PiPServiceRelation_installed = False
config.plugins.virtualzap = ConfigSubsection()
config.plugins.virtualzap.mode = ConfigSelection(default="0", choices = [("0", _("as plugin in extended bar")), ("1", _("with long OK press")), ("2", _("with Exit button")), ("3", _("with Left & Right buttons")), ("4", _("with Up & Down buttons"))])
config.plugins.virtualzap.usepip = ConfigYesNo(default = True)
config.plugins.virtualzap.showpipininfobar = ConfigYesNo(default = True)
config.plugins.virtualzap.saveLastService = ConfigYesNo(default = False)
config.plugins.virtualzap.picons = ConfigYesNo(default = True)
config.plugins.virtualzap.picondir = ConfigDirectory()
config.plugins.virtualzap.curref = ConfigText()
config.plugins.virtualzap.curbouquet = ConfigText()
config.plugins.virtualzap.exittimer =  ConfigInteger(0,limits = (0, 20))

if config.plugins.virtualzap.mode.value == "0" or config.plugins.virtualzap.mode.value == "1":
	def autostart(reason, **kwargs):
		if config.plugins.virtualzap.mode.value != "0":
			# overide InfoBarShowHide
			global InfoBarShowHideINIT
			if InfoBarShowHideINIT is None:
				InfoBarShowHideINIT = InfoBarShowHide.__init__
			InfoBarShowHide.__init__ = InfoBarShowHide__init__
			# new method
			InfoBarShowHide.showVZ = showVZ
			InfoBarShowHide.VirtualZapCallback = VirtualZapCallback
			if config.plugins.virtualzap.mode.value == "2":
				InfoBarShowHide.newHide = newHide

	def InfoBarShowHide__init__(self):
		# initialize InfoBarShowHide with original __init__
		InfoBarShowHideINIT(self)
		# delete current key map --> we have to use "ok" with b-flag
		if config.plugins.virtualzap.mode.value == "1":
			del self["ShowHideActions"]
			# initialize own actionmap with ok = b and longOK = l
			self["myactions"] = ActionMap( ["myShowHideActions"] ,

			{
				"toggleShow": self.toggleShow,
				"longOK": self.showVZ,
				"hide": self.hide,
			}, 1)
		elif config.plugins.virtualzap.mode.value == "2":
			self["ShowHideActions"] = ActionMap( ["InfobarShowHideActions"] ,

			{
				"toggleShow": self.toggleShow,
				"hide": self.newHide,
			}, 1)
			
	def Plugins(**kwargs):
 		if config.plugins.virtualzap.mode.value == "0":
			plist = [PluginDescriptor(name="Virtual Zap", description=_("Virtual (PiP) Zap"), where = PluginDescriptor.WHERE_EXTENSIONSMENU,icon = "plugin.png", fnc = main)]
		elif config.plugins.virtualzap.mode.value == "1" or config.plugins.virtualzap.mode.value == "2":
			plist = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART,fnc = autostart)]
		plist.append(PluginDescriptor(name="Virtual Zap Setup", description=_("Virtual Zap Setup"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc = setup))
		return plist
	
if config.plugins.virtualzap.mode.value == "3" or config.plugins.virtualzap.mode.value == "4":

	baseInfoBarPlugins__init__ = None

	def autostart(reason, **kwargs):
		global baseInfoBarPlugins__init__
		if 'session' in kwargs:
			session = kwargs['session']
			if baseInfoBarPlugins__init__ is None:
				baseInfoBarPlugins__init__ = InfoBarPlugins.__init__
			InfoBarPlugins.__init__ = InfoBarPlugins__init__
			InfoBarPlugins.showVZ = showVZ
			InfoBarPlugins.VirtualZapCallback = VirtualZapCallback
		return
		
	def InfoBarPlugins__init__(self):
		if config.plugins.virtualzap.mode.value == "3":
			from Screens.InfoBarGenerics import InfoBarEPG
			if isinstance(self, InfoBarEPG):
				x = {'showleft': (self.showVZ),
				'showright': (self.showVZ)}
				self['myactions'] = HelpableActionMap(self, 'myShowHideActions', x)
			else:
				InfoBarPlugins.__init__ = InfoBarPlugins.__init__
				InfoBarPlugins.showleft = None
				InfoBarPlugins.showright = None
			baseInfoBarPlugins__init__(self)
			return
		elif config.plugins.virtualzap.mode.value == "4":
			from Screens.InfoBarGenerics import InfoBarEPG
			if isinstance(self, InfoBarEPG):
				x = {'showup': (self.showVZ),
				'showdown': (self.showVZ)}
				self['myactions'] = HelpableActionMap(self, 'myShowHideActions', x)
			else:
				InfoBarPlugins.__init__ = InfoBarPlugins.__init__
				InfoBarPlugins.showup = None
				InfoBarPlugins.showdown = None
			baseInfoBarPlugins__init__(self)
			return
			
	def Plugins(**kwargs):
		plist = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART,fnc = autostart)]
		plist.append(PluginDescriptor(name="Virtual Zap Setup", description=_("Virtual Zap Setup"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc = setup))
		return plist

def showVZ(self):
	from  Screens.InfoBarGenerics import InfoBarEPG
	# check for InfoBarEPG --> only start if true
	if isinstance(self, InfoBarEPG):
		# check for PiP
		if isinstance(self, InfoBarPiP):
			# check if PiP is already shown
			if self.pipShown():
				# it is... close it!
				self.showPiP()
		if isinstance(self, InfoBar):
			self.session.openWithCallback(self.VirtualZapCallback, VirtualZap, self.servicelist)

def VirtualZapCallback(self, service = None, servicePath = None):
	if isinstance(self, InfoBarPiP):
		if service and servicePath:
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			if self.session.pip.playService(service):
				self.session.pipshown = True
				self.session.pip.servicePath = servicePath
			else:
				self.session.pipshown = False
				del self.session.pip
				self.session.openWithCallback(self.close, MessageBox, _("Could not open Picture in Picture"), MessageBox.TYPE_ERROR)

def newHide(self):
	# remember if infobar is shown
	visible = self.shown
	self.hide()
	if not visible:
		# infobar was not shown, start VZ
		self.showVZ()

def setup(session,**kwargs):
	session.open(VirtualZapConfig)

def main(session,**kwargs):
	session.open(VirtualZap, kwargs["servicelist"])

class VirtualZap(Screen):
	sz_w = getDesktop(0).size().width()

	#
	# VirtualZapPicon or VirtualZapPiconNoPiP
	#

	if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value and config.plugins.virtualzap.showpipininfobar.value and config.plugins.virtualzap.picons.value:
		# use PiP in InfobarPicon
		if sz_w == 1280:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapPicon" position="0,505" size="1280,220" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,0" size="1280,220" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="1016,77" size="214,120" zPosition="1"/>
					<widget name="vzPicon" position="100,107" size="100,60" alphatest="blend" zPosition="3"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowNum" position="260,60" size="60,32" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowChannel" position="320,60" size="636,32" transparent="1" zPosition="2"/>
					<widget foregroundColor="#ffffff" name="vzProgress" position="97,602" size="696,3" transparent="1" zPosition="5"/>
					<eLabel backgroundColor="#f4f4f4" position="98,603" size="696,1" zPosition="4"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventStart" position="260,105" size="80,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventTitle" position="355,105" size="465,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventStart" position="260,140" size="80,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventTitle" position="355,140" size="465,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowDuration" position="832,105" size="120,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextDuration" position="832,140" size="120,28" transparent="1" zPosition="2"/>
				</screen>"""
		elif sz_w == 1024:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapPicon" position="0,420" size="1024,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="1024,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,20" size="164,92" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="230,25" size="741,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="230,55" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="230,80" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="850,55" size="124,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="850,80" size="124,25" transparent="1" zPosition="2"/>
				</screen>"""
		else:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZapPicon" position="0,420" size="720,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="720,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,25" size="130,73" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="190,25" size="480,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="190,55" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="190,80" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="550,55" size="120,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="550,80" size="120,25" transparent="1" zPosition="2"/>
				</screen>"""
				
	elif SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value and config.plugins.virtualzap.showpipininfobar.value and not config.plugins.virtualzap.picons.value:
		# use PiP in Infobar
		if sz_w == 1280:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,505" size="1280,220" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,0" size="1280,220" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="60,50" size="214,120" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowNum" position="305,60" size="60,32" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowChannel" position="390,60" size="670,32" transparent="1" zPosition="2"/>
					<widget foregroundColor="#ffffff" name="vzProgress" position="305,602" size="885,3" transparent="1" zPosition="5"/>
					<eLabel backgroundColor="#f4f4f4" position="305,603" size="885,1" zPosition="4"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventStart" position="305,105" size="80,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventTitle" position="390,105" size="670,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventStart" position="305,140" size="80,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventTitle" position="390,140" size="670,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowDuration" position="1070,105" size="120,28" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextDuration" position="1070,140" size="120,28" transparent="1" zPosition="2"/>
				</screen>"""
		elif sz_w == 1024:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,420" size="1024,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="1024,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,20" size="164,92" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="230,25" size="741,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="230,55" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="230,80" size="600,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="850,55" size="124,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="850,80" size="124,25" transparent="1" zPosition="2"/>
				</screen>"""
		else:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" name="VirtualZap" position="0,420" size="720,176" title="Virtual Zap">
					<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,0" size="720,176" zPosition="0"/>
					<widget backgroundColor="transparent" name="video" position="50,25" size="130,73" zPosition="1"/>
					<widget backgroundColor="#101214" font="Regular;22" halign="left" name="NowChannel" position="190,25" size="480,30" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="190,55" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="190,80" size="360,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="550,55" size="120,25" transparent="1" zPosition="2"/>
					<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="550,80" size="120,25" transparent="1" zPosition="2"/>
				</screen>"""
	else:
		if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value and not config.plugins.virtualzap.showpipininfobar.value:
			# use standard PiP
			config.av.pip = ConfigPosition(default=[0, 0, 0, 0], args = (719, 567, 720, 568))
			x = config.av.pip.value[0]
			y = config.av.pip.value[1]
			w = config.av.pip.value[2]
			h = config.av.pip.value[3]
		else:
			# no PiP
			x = 0
			y = 0
			w = 0
			h = 0

		if config.plugins.virtualzap.picons.value:
			if sz_w == 1280:
				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapPiconNoPiP" position="0,0" size="1280,720" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<widget name="vzPicon" position="100,612" size="100,60" alphatest="blend" zPosition="3"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,505" size="1280,220" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowNum" position="260,565" size="60,32" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowChannel" position="320,565" size="820,32" transparent="1" zPosition="2"/>
						<widget foregroundColor="#ffffff" name="vzProgress" position="260,602" size="880,3" transparent="1" zPosition="5"/>
						<eLabel backgroundColor="#f4f4f4" position="260,603" size="880,1" zPosition="4"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventStart" position="260,610" size="80,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventTitle" position="355,610" size="645,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventStart" position="260,645" size="80,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventTitle" position="355,645" size="645,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowDuration" position="1015,610" size="124,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextDuration" position="1015,645" size="124,28" transparent="1" zPosition="2"/>
					</screen>""" % (x,y,w,h)
			elif sz_w == 1024:
				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapPiconNoPiP" position="0,0" size="1024,576" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,420" size="1024,176" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="100,445" size="824,30" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="100,475" size="700,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="100,500" size="700,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="800,475" size="124,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="800,500" size="124,25" transparent="1" zPosition="2"/>
					</screen>""" % (x,y,w,h)
			else:

				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapPiconNoPiP" position="0,0" size="720,576" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,420" size="720,176" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="50,445" size="620,30" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="50,475" size="500,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="50,500" size="500,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="550,475" size="120,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="550,500" size="120,25" transparent="1" zPosition="2"/>
					</screen>"""  % (x,y,w,h)
				
		else:
			if sz_w == 1280:
				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,0" size="1280,720" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/hd.png" position="0,505" size="1280,220" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowNum" position="140,565" size="60,32" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;26" halign="center" name="NowChannel" position="245,645" size="820,32" transparent="1" zPosition="2"/>
						<widget foregroundColor="#ffffff" name="vzProgress" position="140,602" size="1000,3" transparent="1" zPosition="5"/>
						<eLabel backgroundColor="#f4f4f4" position="140,603" size="1000,1" zPosition="4"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventStart" position="140,610" size="80,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="left" name="NowEventTitle" position="225,610" size="765,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventStart" position="140,645" size="80,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="left" name="NextEventTitle" position="225,645" size="765,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" foregroundColor="#fcc000" halign="right" name="NowDuration" position="1015,610" size="124,28" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;24" halign="right" name="NextDuration" position="1015,645" size="124,28" transparent="1" zPosition="2"/>
					</screen>""" % (x,y,w,h)
			elif sz_w == 1024:
				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,0" size="1024,576" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,420" size="1024,176" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="100,445" size="824,30" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="100,475" size="700,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="100,500" size="700,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="800,475" size="124,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="800,500" size="124,25" transparent="1" zPosition="2"/>
					</screen>""" % (x,y,w,h)
			else:
				skin = """
					<screen backgroundColor="transparent" flags="wfNoBorder" name="VirtualZapNoPiP" position="0,0" size="720,576" title="Virtual Zap">
						<widget backgroundColor="transparent" name="video" position="%d,%d" size="%d,%d" zPosition="1"/>
						<ePixmap alphatest="off" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/VirtualZap/sd.png" position="0,420" size="720,176" zPosition="0"/>
						<widget backgroundColor="#101214" font="Regular;22" halign="center" name="NowChannel" position="50,445" size="620,30" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="left" name="NowEPG" position="50,475" size="500,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="left" name="NextEPG" position="50,500" size="500,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" foregroundColor="#fcc000" halign="right" name="NowDuration" position="550,475" size="120,25" transparent="1" zPosition="2"/>
						<widget backgroundColor="#101214" font="Regular;20" halign="right" name="NextDuration" position="550,500" size="120,25" transparent="1" zPosition="2"/>
					</screen>"""  % (x,y,w,h)

	def __init__(self, session, servicelist = None):
		Screen.__init__(self, session)
		self.session = session
		if SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value and config.plugins.virtualzap.showpipininfobar.value and config.plugins.virtualzap.picons.value:
			self.skinName = "VirtualZapPicon"
			self.pipAvailable = True
		elif SystemInfo.get("NumVideoDecoders", 1) > 1 and config.plugins.virtualzap.usepip.value and config.plugins.virtualzap.showpipininfobar.value and not config.plugins.virtualzap.picons.value:
			self.skinName = "VirtualZap"
			self.pipAvailable = True
		else:
			if config.plugins.virtualzap.picons.value:
				self.skinName = "VirtualZapPiconNoPiP"
				self.pipAvailable =  (SystemInfo.get("NumVideoDecoders", 1) > 1)  and config.plugins.virtualzap.usepip.value and not config.plugins.virtualzap.showpipininfobar.value
			else:
				self.skinName = "VirtualZapNoPiP"
				self.pipAvailable =  (SystemInfo.get("NumVideoDecoders", 1) > 1)  and config.plugins.virtualzap.usepip.value and not config.plugins.virtualzap.showpipininfobar.value
					
		self.epgcache = eEPGCache.getInstance()
		self.CheckForEPG = eTimer()
		self.CheckForEPG.callback.append(self.CheckItNow)
		
		self.defpicon = None
		if config.plugins.virtualzap.picons.value:
			for scope, path in [(SCOPE_CURRENT_SKIN, "picon_default.png"), (SCOPE_SKIN_IMAGE, "skin_default/picon_default.png")]:
				tmp = resolveFilename(scope, path)
				if pathExists(tmp) and getSize(tmp):
					self.defpicon = tmp
					break

		self["NowChannel"] = Label()
		self["NowNum"] = Label()
		self["NowEPG"] = Label() # Only for backward compatibility
		self["NextEPG"] = Label() # Only for backward compatibility
		self["NowEventStart"] = Label()
		self["NextEventStart"] = Label()
		self["NowEventEnd"] = Label()
		self["NextEventEnd"] = Label()
		self["NowEventTitle"] = Label()
		self["NextEventTitle"] = Label()
		self["NowTime"] = Label() # Only for backward compatibility
		self["NextTime"] = Label() # Only for backward compatibility
		self["NowDuration"] = Label()
		self["NextDuration"] = Label()
		self["vzPicon"] = Pixmap()
		self["vzProgress"] = ProgressBar()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ChannelSelectBaseActions", "ChannelSelectEPGActions", "ColorActions"], 
		{
			"ok": self.ok, 
			"cancel": self.closing,
			"right": self.nextService,
			"left": self.prevService,
			"nextBouquet": self.showFavourites,
			"prevBouquet": self.openServiceList,
			"showEPGList": self.openEventView,
			"blue": self.standardPiP,
			"yellow": self.switchAndStandardPiP,
			"down": self.switchChannelDown,
			"up": self.switchChannelUp,
		},-2)
		self["actions2"] = NumberActionMap(["NumberActions"],
		{
			"0": self.swap,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutReady)
		
		# PiP
		if self.pipAvailable:
			# activate PiP support
			if config.plugins.virtualzap.usepip.value and not config.plugins.virtualzap.showpipininfobar.value:
				# activate standard PiP
				self["video"] = VideoWindow()
			else:
				# show PiP in Infobar
				self["video"] = VideoWindow(fb_width = getDesktop(0).size().width(), fb_height = getDesktop(0).size().height())
			self.currentPiP = ""
		else:
			# no PiP
			self["video"] = Label()
		# this is the servicelist from ChannelSelectionBase
		self.servicelist = servicelist
		# save orig. method of zap in servicelist
		self.servicelist_orig_zap = self.servicelist.zap 
		# when displaying ChannelSelection, do not zap when pressing "ok", so new method is needed	
		self.servicelist.zap = self.servicelist_overwrite_zap
		# overwrite the actionmap of ChannelSelection
		self.servicelist["actions"] = ActionMap(["OkCancelActions"],
			{
				"cancel": self.cancelChannelSelection,
				"ok": self.servicelist.channelSelected,
			})
		# temp. vars, needed when pressing cancel in ChannelSelection
		self.curSelectedRef = None
		self.curSelectedBouquet = None
		# needed, because if we won't zap, we have to go back to the current bouquet and service
		self.curRef = ServiceReference(self.servicelist.getCurrentSelection())
		self.curBouquet = self.servicelist.getRoot()
		# start with last used service
		if config.plugins.virtualzap.saveLastService.value:
			# get service and bouquet ref
			ref = eServiceReference(config.plugins.virtualzap.curref.value)
			bouquet = eServiceReference(config.plugins.virtualzap.curbouquet.value)
			if ref.valid() and bouquet.valid():
				# select bouquet and ref in servicelist
				self.setServicelistSelection(bouquet, ref)
		# prepare exitTimer
		self.exitTimer = eTimer()
		self.exitTimer.timeout.get().append(self.standardPiP)
		# reverse changes of ChannelSelection when closing plugin
		self.onClose.append(self.__onClose)
		# if PiPServiceRelation is installed, get relation dict
		if plugin_PiPServiceRelation_installed:
			self.pipServiceRelation = getRelationDict()
		else:
			self.pipServiceRelation = {}
		
	def onLayoutReady(self):
		self.updateInfos()

	def resetExitTimer(self):
		# if enabled, run exit timer
		if config.plugins.virtualzap.exittimer.value != 0:
			if self.exitTimer.isActive():
				self.exitTimer.stop()
			self.exitTimer.start(config.plugins.virtualzap.exittimer.value * 1000)

	def nextService(self):
		# get next service
		if self.servicelist.inBouquet():
			prev = self.servicelist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
						self.servicelist.nextBouquet()
					else:
						self.servicelist.moveDown()
					cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			self.servicelist.moveDown()
		if self.isPlayable():
			self.updateInfos()
		else:
			self.nextService()

	def prevService(self):
		# get previous service
		if self.servicelist.inBouquet():
			prev = self.servicelist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value:
						if self.servicelist.atBegin():
							self.servicelist.prevBouquet()
					self.servicelist.moveUp()
					cur = self.servicelist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			self.servicelist.moveUp()
		if self.isPlayable():
			self.updateInfos()
		else:
			self.prevService()

	def isPlayable(self):
		# check if service is playable
		current = ServiceReference(self.servicelist.getCurrentSelection())
		return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))


	def nextBouquet(self):
		# next bouquet with first service
		if config.usage.multibouquet.value:
			self.servicelist.nextBouquet()
		self.updateInfos()

	def prevBouquet(self):
		# previous bouquet with first service
		if config.usage.multibouquet.value:
			self.servicelist.prevBouquet()
		self.updateInfos()


	def updateInfos(self):
		self.resetExitTimer()
		# update data
		current = ServiceReference(self.servicelist.getCurrentSelection())
		num = str(self.servicelist.getCurrentSelection().getChannelNum())
		self["NowChannel"].setText(current.getServiceName())
		self["NowNum"].setText(num)
		nowepg, nowstart, nowend, nowname, nowduration, percentnow = self.getEPGNowNext(current.ref,0)
		nextepg, nextstart, nextend, nextname, nextduration, percentnext = self.getEPGNowNext(current.ref,1)
		self["NowEventStart"].setText(nowstart)
		self["NextEventStart"].setText(nextstart)
		self["NowEventEnd"].setText(nowend)
		self["NextEventEnd"].setText(nextend)
		self["NowEventTitle"].setText(nowname)
		self["NextEventTitle"].setText(nextname)
		self["NowEPG"].setText(nowepg) # Only for backward compatibility
		self["NextEPG"].setText(nextepg) # Only for backward compatibility
		self["NowTime"].setText(nowduration) # Only for backward compatibility
		self["NextTime"].setText(nextduration) # Only for backward compatibility
		self["NowDuration"].setText(nowduration)
		self["NextDuration"].setText(nextduration)
		self["vzProgress"].setValue(percentnow)

		if config.plugins.virtualzap.picons.value:
			pngname = self.defpicon
			service = self.servicelist.getCurrentSelection()
			if service:
				sname = service.toString()
				sname = ':'.join(sname.split(':')[:11])
				pos = sname.rfind(':')
				if pos != -1:
					sname = sname[:pos].rstrip(':').replace(':','_')
					sname = config.plugins.virtualzap.picondir.value + sname + '.png'
					if pathExists(sname):
						pngname = sname
			self["vzPicon"].instance.setPixmapFromFile(pngname)

		if not nowepg:
			# no epg found --> let's try it again, but only if PiP is activated
			if self.pipAvailable:
				self.CheckForEPG.start(3000, True)
		if self.pipAvailable:
			# play in videowindow
			self.playService(current.ref)

	def getProgressbar(self, configElement = None):
		self["vzProgress"].show()
		value = self["vzProgress"].getValue()
		self["vzProgress"].setValue(0)
		self["vzProgress"].setValue(value)
		
	def getEPGNowNext(self, ref, modus):
		# get now || next event
		if self.epgcache is not None:
			event = self.epgcache.lookupEvent(['IBDCT', (ref.toString(), modus, -1)])
			if event:
				if event[0][4]:
					t = localtime(event[0][1])
					begin = event[0][1]
					duration = event[0][2]
					now = int(time())
					if modus == 0:
						eventduration =_("+%d min") % (((event[0][1] + duration) - time()) / 60)
						percent = int((now - begin) * 100 / duration)
						eventname = event[0][4]
						eventstart = strftime("%H:%M", localtime(begin))
						eventend = strftime("%H:%M", localtime(begin + duration))
						eventtimename = ("%02d:%02d   %s") % (t[3],t[4], event[0][4])
					elif modus == 1:
						eventduration =_("%d min") % (duration / 60)
						percent = 0
						eventname = event[0][4]
						eventstart = strftime("%H:%M", localtime(begin))
						eventend = strftime("%H:%M", localtime(begin + duration))
						eventtimename = ("%02d:%02d   %s") % (t[3],t[4], event[0][4])
					return eventtimename, eventstart, eventend, eventname, eventduration, percent
				else:
					return _("No EPG data"), "", "", _("No EPG data"), "", ""
		return _("No EPG data"), "", "", _("No EPG data"), "", ""
	
	def openSingleServiceEPG(self):
		# show EPGList
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self.session.open(EPGSelection, current.ref)

	def openEventView(self):
		# stop exitTimer
		if self.exitTimer.isActive():
			self.exitTimer.stop()
		# show EPG Event
		epglist = [ ]
		self.epglist = epglist
		service = ServiceReference(self.servicelist.getCurrentSelection())
		ref = service.ref
		evt = self.epgcache.lookupEventTime(ref, -1)
		if evt:
			epglist.append(evt)
		evt = self.epgcache.lookupEventTime(ref, -1, 1)
		if evt:
			epglist.append(evt)
		if epglist:
			self.session.openWithCallback(self.EventViewEPGSelectCallBack, EventViewEPGSelect, epglist[0], service, self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)

	def EventViewEPGSelectCallBack(self):
		# if enabled, start ExitTimer
		self.resetExitTimer()

	def eventViewCallback(self, setEvent, setService, val):
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

	def openMultiServiceEPG(self):
		# not supported
		pass

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def setServicelistSelection(self, bouquet, service):
		# we need to select the old service with bouquet
		if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
			self.servicelist.clearPath()
			self.servicelist.enterPath(self.servicelist.bouquet_root)
			self.servicelist.enterPath(bouquet)
		self.servicelist.setCurrentSelection(service) #select the service in servicelist

	def closing(self):
		if self.pipAvailable:
			self.pipservice = None
		# save last used service and bouqet ref
		self.saveLastService(self.servicelist.getCurrentSelection().toString(), self.servicelist.getRoot().toString())
		# select running service in servicelist again
		self.setServicelistSelection(self.curBouquet, self.curRef.ref)
		self.close()
			
	def ok(self):
		# we have to close PiP first, otherwise the service-display is freezed
		if self.pipAvailable:
			self.pipservice = None
		# play selected service and close virtualzap
		self.servicelist_orig_zap()
		# save last used service and bouqet ref
		self.saveLastService(self.curRef.ref.toString(), self.curBouquet.toString())
		self.close()

	def standardPiP(self):
		if not self.pipAvailable:
			return
		# close PiP
		self.pipservice = None
		# save current selected service for standard PiP
		service = ServiceReference(self.servicelist.getCurrentSelection()).ref
		servicePath = self.servicelist.getCurrentServicePath() # same bug as in channelselection
		# save last used service and bouqet ref
		self.saveLastService(self.servicelist.getCurrentSelection().toString(), self.servicelist.getRoot().toString())
		# select running service in servicelist
		self.setServicelistSelection(self.curBouquet, self.curRef.ref)
		# close VZ and start standard PiP
		self.close(service, servicePath)

	def switchAndStandardPiP(self):
		if not self.pipAvailable:
			return
		self.pipservice = None
		# save current selected servicePath for standard PiP
		servicePath = self.servicelist.getCurrentServicePath()
		# save last used service and bouqet ref
		self.saveLastService(self.curRef.ref.toString(), self.curBouquet.toString())
		# play selected service
		self.servicelist_orig_zap()
		# close VZ and start standard PiP
		self.close(self.curRef.ref, servicePath)

	def saveLastService(self, ref, bouquet):
		if config.plugins.virtualzap.saveLastService.value:
			# save last VZ service
			config.plugins.virtualzap.curref.value = ref
			config.plugins.virtualzap.curbouquet.value = bouquet
			config.plugins.virtualzap.save()
		# stop exitTimer
		if self.exitTimer.isActive():
			self.exitTimer.stop()

	def CheckItNow(self):
		self.CheckForEPG.stop()
		self.updateInfos()

	# if available play service in PiP 
	def playService(self, service):
		if parentalControl.getProtectionLevel(service.toCompareString()) == -1 or (parentalControl.configInitialized and parentalControl.sessionPinCached and parentalControl.sessionPinCachedValue): # check parentalControl, only play a protected service when Pin-Cache is activated and still valid
			current_service = service
			n_service = self.pipServiceRelation.get(service.toString(),None) # PiPServiceRelation
			if n_service is not None:
				service = eServiceReference(n_service)
			if service and (service.flags & eServiceReference.isGroup):
				ref = getBestPlayableServiceReference(service, eServiceReference())
			else:
				ref = service
			if ref and ref.toString() != self.currentPiP:
				self.pipservice = eServiceCenter.getInstance().play(ref)
				if self.pipservice and not self.pipservice.setTarget(1):
					self.pipservice.start()
					self.currentPiP = current_service.toString()
				else:
					self.pipservice = None
					self.currentPiP = ""
		else:
			self.pipservice = None
			self.currentPiP = ""

	# switch with numbers
	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number, self.searchNumber)

	def numberEntered(self, service = None, bouquet = None):
		if service:
			self.selectAndStartService(service, bouquet)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if servicelist:
			serviceIterator = servicelist.getNext()
			while serviceIterator.valid():
				if num == serviceIterator.getChannelNum():
					return serviceIterator
				serviceIterator = servicelist.getNext()
		return None

	def searchNumber(self, number, firstBouquetOnly = False):
		bouquet = self.servicelist.getRoot()
		service = None
		serviceHandler = eServiceCenter.getInstance()
		if not firstBouquetOnly:
			service = self.searchNumberHelper(serviceHandler, number, bouquet)
		if config.usage.multibouquet.value and not service:
			bouquet = self.servicelist.bouquet_root
			bouquetlist = serviceHandler.list(bouquet)
			if bouquetlist:
				bouquet = bouquetlist.getNext()
				while bouquet.valid():
					if bouquet.flags & eServiceReference.isDirectory:
						service = self.searchNumberHelper(serviceHandler, number, bouquet)
						if service:
							playable = not (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)) or (service.flags & eServiceReference.isNumberedMarker)
							if not playable:
								service = None
							break
						if config.usage.alternative_number_mode.value or firstBouquetOnly:
							break
					bouquet = bouquetlist.getNext()
		return service, bouquet

	def selectAndStartService(self, service, bouquet):
		if service:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
			self.servicelist.zap(enable_pipzap = True)
		self.updateInfos()
		
	def zapToNumber(self, number):
		service, bouquet = self.searchNumber(number)
		self.selectAndStartService(service, bouquet)
		
	def swap(self, number):
		# save old values for selecting it in servicelist after zapping
		currentRef = self.curRef
		currentBouquet = self.curBouquet
		# we have to close PiP first, otherwise the service-display is freezed
		if self.pipAvailable:
			self.pipservice = None
		# zap and set new values for the new reference and bouquet
		self.servicelist_orig_zap()
		self.curRef = ServiceReference(self.servicelist.getCurrentSelection())
		self.curBouquet = self.servicelist.getRoot()
		# select old values in servicelist
		self.setServicelistSelection(currentBouquet, currentRef.ref)
		# play old service in PiP
		self.updateInfos()

	# ChannelSelection Support
	def prepareChannelSelectionDisplay(self):
		# stop exitTimer
		if self.exitTimer.isActive():
			self.exitTimer.stop()
		# turn off PiP
		if self.pipAvailable:
			self.pipservice = None
		# save current ref and bouquet ( for cancel )
		self.curSelectedRef = eServiceReference(self.servicelist.getCurrentSelection().toString())
		self.curSelectedBouquet = self.servicelist.getRoot()

	def cancelChannelSelection(self):
		# select service and bouquet selected before started ChannelSelection
		if self.servicelist.revertMode is None:
			ref = self.curSelectedRef
			bouquet = self.curSelectedBouquet
			if ref.valid() and bouquet.valid():
				# select bouquet and ref in servicelist
				self.setServicelistSelection(bouquet, ref)
		# close ChannelSelection
		self.servicelist.revertMode = None
		self.servicelist.close(None)

		# clean up
		self.curSelectedRef = None
		self.curSelectedBouquet = None
		# display VZ data
		self.servicelist_overwrite_zap()

	def switchChannelDown(self):
		self.prepareChannelSelectionDisplay()
		self.servicelist.moveDown()
		# show ChannelSelection
		self.session.execDialog(self.servicelist)

	def switchChannelUp(self):
		self.prepareChannelSelectionDisplay()
		self.servicelist.moveUp()
		# show ChannelSelection
		self.session.execDialog(self.servicelist)

	def showFavourites(self):
		self.prepareChannelSelectionDisplay()
		self.servicelist.showFavourites()
		# show ChannelSelection
		self.session.execDialog(self.servicelist)

	def openServiceList(self):
		self.prepareChannelSelectionDisplay()
		# show ChannelSelection
		self.session.execDialog(self.servicelist)

	def servicelist_overwrite_zap(self, *args, **kwargs):
		# we do not really want to zap to the service, just display data for VZ
		self.currentPiP = ""
		if self.isPlayable():
			self.updateInfos()

	def __onClose(self):
		# reverse changes of ChannelSelection 
		self.servicelist.zap = self.servicelist_orig_zap
		self.servicelist["actions"] = ActionMap(["OkCancelActions", "TvRadioActions"],
			{
				"cancel": self.servicelist.cancel,
				"ok": self.servicelist.channelSelected,
				"keyRadio": self.servicelist.setModeRadio,
				"keyTV": self.servicelist.setModeTv,
			})
			
class DirectoryBrowserVZ(Screen):
	skin = """<screen name="DirectoryBrowserVZ" position="center,center" size="520,440" title=" " >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="curdir" render="Label" position="5,50" size="510,20"  font="Regular;20" halign="left" valign="center" backgroundColor="background" transparent="1" noWrap="1" />
			<widget name="filelist" position="5,80" size="510,345" scrollbarMode="showOnDemand" />
		</screen>"""
	
	def __init__(self, session, curdir, matchingPattern=None):
		Screen.__init__(self, session)

		self["Title"].setText(_("Directory browser"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["curdir"] = StaticText(_("current:  %s")%(curdir or ''))

		self.filelist = FileList(curdir, matchingPattern=matchingPattern, enableWrapAround=True)
		self.filelist.onSelectionChanged.append(self.__selChanged)
		self["filelist"] = self.filelist

		self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"green": self.keyGreen,
				"red": self.keyRed,
				"ok": self.keyOk,
				"cancel": self.keyRed
			})
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		#self.setTitle(_("Directory browser"))
		pass

	def getCurrentSelected(self):
		dirname = self.filelist.getCurrentDirectory()
		filename = self.filelist.getFilename()
		if not filename and not dirname:
			cur = ''
		elif not filename:
			cur = dirname
		elif not dirname:
			cur = filename
		else:
			if not self.filelist.canDescent() or len(filename) <= len(dirname):
				cur = dirname
			else:
				cur = filename
		return cur or ''

	def __selChanged(self):
		self["curdir"].setText(_("current:  %s")%(self.getCurrentSelected()))

	def keyOk(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def keyGreen(self):
		self.close(self.getCurrentSelected())

	def keyRed(self):
		self.close(False)

class VirtualZapConfig(Screen, ConfigListScreen):

	skin = """
		<screen position="center,center" size="560,400" title="Virtual Zap Config" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="520,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.onChangedEntry = [ ]
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.setTitle(_("Virtual Zap Config"))
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session, on_change = self.changedEntry)
		self.createSetup()
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keyOk,
		}, -2)
		
	def createSetup(self):
		self.list = [ ]
		self.list.append(getConfigListEntry(_("Usage"), config.plugins.virtualzap.mode))
		self.list.append(getConfigListEntry(_("Show picons"), config.plugins.virtualzap.picons))
		if config.plugins.virtualzap.picons.value:
			self.list.append(getConfigListEntry(_("Picon path"), config.plugins.virtualzap.picondir))
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			self.list.append(getConfigListEntry(_("Use PiP"), config.plugins.virtualzap.usepip))
			self.list.append(getConfigListEntry(_("Show PiP in Infobar"), config.plugins.virtualzap.showpipininfobar))
			self.list.append(getConfigListEntry(_("Start standard PiP after x secs (0 = disabled)"), config.plugins.virtualzap.exittimer))
		self.list.append(getConfigListEntry(_("Remember last service"), config.plugins.virtualzap.saveLastService))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
			
	def keyLeft(self):	
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()
		
	def keyOk(self):
		ConfigListScreen.keyOK(self)
		sel = self["config"].getCurrent()[1]
		if sel == config.plugins.virtualzap.picondir:
			self.session.openWithCallback(self.directoryBrowserClosed, DirectoryBrowserVZ, config.plugins.virtualzap.picondir.value, "^.*\.png")
#			self.close()
			
	def directoryBrowserClosed(self, path):
		if path != False:
			config.plugins.virtualzap.picondir.setValue(path)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply the new settings.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))
		

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()
