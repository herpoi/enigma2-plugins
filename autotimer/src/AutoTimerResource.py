from twisted.web import http, resource
from AutoTimer import AutoTimer
from . import _

# pretty basic resource which is just present to have a way to start a
# forced run through the webif
class AutoTimerResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		from plugin import autotimer

		remove = False
		res = False
		if autotimer is None:
			autotimer = AutoTimer()
			remove = True

		if req.args.has_key("parse"):
			ret = autotimer.parseEPG()
			output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified.") % (ret[0], ret[1], ret[2])
			res = True
		else:
			output = "unknown command"

		if remove:
			autotimer.writeXml()
			autotimer = None

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if res else 'false', output)
	
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return result
