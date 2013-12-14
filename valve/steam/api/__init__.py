
"""
	Provides an dynamic interface to the Steam Web API. Making requests
	is fairly well abstracted, however responses are essentially left
	as they're recevied.
	
	Many of the available interfaces require an API key which can be
	got from http://steamcommunity.com/dev/apikey
	
	Useful reading:
		https://developer.valvesoftware.com/wiki/Steam_Web_API
		http://wiki.teamfortress.com/wiki/WebAPI
"""

import urllib
import urllib2
import urlparse
import re
import json
import xml.etree.ElementTree
import keyword
import warnings

API_LIST_REQUEST = ("GET", "ISteamWebAPIUtil/GetSupportedAPIList/v0001/", {})

appid_name_map = {
	"440": "tf2",
	"520": "tf2_beta",
	"570": "dota2",
	"620": "portal2",
	"730": "csgo",
	"816": "dota2_private_beta",
	"841": "portal2_beta",
	"205790": "dota2_test",
}

def _pythonise_name(name):
	"""
		Attempts to convert Steam API interfance and method names to
		more Python-like equivalents. Returns a list of aliases for the
		given name.
	"""
	
	# See http://stackoverflow.com/a/1176023/122531 for de-camelcasing
	names = []
	
	s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
	s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
	s3 = re.sub(r"^i_", r"", s2).lower()
	s4 = re.sub(r"^steam_", r"", s3)
	names.append(s4)
	
	try:
		s5 = re.sub(r"(\d+)$", appid_name_map[re.findall(r"_(\d+)$", s4)[0]], s4)
		
		# Special case for Portal 2 names, which end up being converted to
		# the likes of portal2_leaderboards_portal2_beta
		# Leading 'portal2_' will be stripped if 'portal2' occurs anywhere else
		# in string.
		if len(re.findall(r"portal2", s5)) > 1:
			s6 = re.sub(r"^portal2_", r"", s5)
			names.append(s6)
		else:
			names.append(s5)
					
	except (KeyError, IndexError):
		pass
	
	return names

class SteamError(Exception): pass

class Parameter(object):
	
	def __init__(self, **config):
		
		self.name = config["name"]
		self.is_optional = config["optional"]
		self.description = config["description"]
		self.type = config["type"]

		self.keyword = re.sub(r"\[\d+\]$", r"", self.name).lower()
		if self.keyword in keyword.kwlist:
			self.keyword += "_"
	
	def validate(self, value):
		
		if self.type == "uint32":
			value = int(value)
			if not 0 <= value < 2**32:
				raise ValueError("Invalid value {val} for parameter '{name}' with type {type}".format(name=self.name, type=self.type, val=value))
			
			return str(value)
		
		elif self.type == "int32":
			value = int(value)
			if -2**31 < value < 2**31:
				raise ValueError("Invalid value {val} for parameter '{name}' with type {type}".format(name=self.name, type=self.type, val=value))
			
			return str(value)
			
		elif self.type == "uint64":
			value = int(value)
			if not 0 <= value < 2**64:
				raise ValueError("Invalid value {val} for parameter '{name}' with type {type}".format(name=self.name, type=self.type, val=value))
				
			return str(value)
		
		elif self.type == "bool":
			return int(bool(value))	
		
		elif self.type == "string":
			return str(value)
		
		elif self.type == "rawbinary":
			return str(value)
		
		else:
			raise NotImplementedError("No conversion avilable for type {}".format(self.type))
	
class InterfaceMethod(object):
	
	def __init__(self, interface, **config):
		
		self.interface = interface
		
		self.name = config["name"]
		self.version = config["version"]
		self.http_method = config["httpmethod"]
		self.parameters = []
		
		for param_config in config["parameters"]:
			if param_config["name"] != "key":
				self.parameters.append(Parameter(**param_config))
			
		#self.__doc__ = "\n".join([
							#"Implementes {}/{}".format(self.interface.name, self.name),
							#"",
							#"Parameters:",
							#] + [
							#"  '{}' -- {}".format(p.name, p.description) for p in self.parameters
							#])
	
	def __repr__(self):
		return "{cls}({iname}.{name})".format(cls=self.__class__.__name__, iname=self.interface.name, name=self.name)
	
	def __call__(self, **params):
		"""
			Builds the request path, validates the parameters, makes the
			actual request and returns the response for the interface method.
		"""

		path = "/{iname}/{mname}/v{ver:04d}/".format(
				iname=self.interface.name,
				mname=self.name,
				ver=self.version
				)
		
		validated_params = []
		for mparam in self.parameters:
			try:
				validated_params.append((
						mparam.name,
						mparam.validate(params[mparam.keyword])
						))
			except KeyError:
				if not mparam.is_optional:
					raise ValueError("Required parameter '{pname}' for {meth} not given".format(pname=mparam.keyword, meth=self))
		
		return self.interface.api.request(self.http_method, path, dict(validated_params))
	
class Interface(object):
	
	def __init__(self, api, **config):
		
		self.api = api
		
		self.name = config["name"]
		self.methods = {}
		
		for method_config in config["methods"]:
			method = InterfaceMethod(self, **method_config)
			if method.name in self.methods:
				warnings.warn("Multiple versions of {}; using version {}".format(
								method,
								max(method.version, self.methods[method.name].version)),
									DeprecationWarning)
				if method.version < self.methods[method.name].version:
					continue
			
			for name in [method.name] + _pythonise_name(method.name):
				self.methods[name] = method
	
	def __repr__(self):
		return "{cls}({name})".format(cls=self.__class__.__name__, name=self.name)
	
	def __getattr__(self, attr):
		
		try:
			return self.methods[attr]
		except KeyError:
			raise AttributeError("{name} interface has no attribute or method called {attr}".format(name=self.name, attr=attr))
	
class SteamAPI(object):
	
	def __init__(self, key=None, format="json",
					url="http://api.steampowered.com/"):
		"""
			Returns a Steam object used for accessing the Steam web API.
			https://developer.valvesoftware.com/wiki/Steam_Web_API
			
				key -- Steam API key; if not specified only a restricted
					set of interfaces will be available
					
				format -- The response format, can be either "json", 
					"xml" or "vdf"
					
				url -- Base URL (scheme + net-location) of the API;
					shouldn't ever need to be chnaged
			
			The nature in which this module is implemented means there's
			no concrete interfaces. Rather they are generated at
			runtime from the api_spec_src, e.g.
			
			http://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v0001/
			
			This file is parsed and a set of interfaces (instances of the
			Interface class) are generated. These in turn generate and
			expose a series of methods as defined in the api_spec_src.
			
			Once the Steam object is created, the interfaces and their
			methods are accessible as if they were regular attributes.
			For example:
			
				Steam().InterfaceName.MethodName()
				
			The names of the interfaces and methods are also defined
			within the api_spec_src. However, the names used are somewhat
			'unpythonic' -- ISteamNews.GetNewsForApp(). Whilst constructing
			the inerfaces and methods an attempt is made to covert the names
			to those which closer resemble what'd you expect from Python --
			news.get_news_for_app(). Both of these names are exposed
			as attributes so either can be used, but it's recommended that
			the same name is used consistently throughout your application.
			
			The rules for name rewriting are:
			
				- CamelCase is converted to camel_case
				
				- Leading 'ISteam' are stripped away
				
				- Trailing app IDs (IGCVersion_440) are converted to
				symbolic names (igc_version_tf2); see `appid_name_map`
				for specific conversions
				
				Note: although names with the app ID replaced with
				symbolic names are exposed, the original name *with* the
				app ID are also made available. This applies in cases
				where there was no known symbolic name for the app ID
				and those that were successfully coverted.
				
				i.e. 'igc_version_440' and 'igc_version_tf2' are both valid
				
				- Leading 'IPortal2' is stripped if 'portal2' occurs
				elsewhere in the name, e.g. 'IPortal2Leaderboards_841'
				becomes 'leaderboards_portal2_beta' *not*
				'portal2_leaderboards_portal2_beta'
				
			Methods accept various key-value pairs as parameters as
			defined in the api_spec_src. These parameters will be passed
			along with the query after being validated and converted
			to the appropriate type.
			
			When a interface method is called a URL is constructed and
			the request is made. The response to the query is returned
			effectively unaltered. Very little abstraction can be done
			at this point as the return format is not defined within
			the api_spec_src. For JSON responses a dictionary is returned,
			as given by json.load(). For XML an 
			xml.etree.ElementTree.ElementTree object is returned which 
			represents the root of the document. VDF responses are simply
			returned as received (string).
			
			Note: interface methods are not 'true methods' in the sense
			that they are functions bound to a class instance. Rather
			they are callable attribute that happen to hold a reference
			to the instance.
			
			Note: if multiple versions of a single interface method exists,
			such as in the case of ISteamUser.GetPlayerSummaries, only 
			the most 'current' one will be available. DeprecationWarnings
			are raised when conflicting versions are found.
		"""
		
		self.key = key
		self.url = url
		self.format = "json"
		self.api_spec = self.request(*API_LIST_REQUEST)
		self.format = format
		
		self.interfaces = {}
		for interface_config in self.api_spec["apilist"]["interfaces"]:
			interface = Interface(self, **interface_config)
			for name in [interface.name] + _pythonise_name(interface.name):
				self.interfaces[name] = interface
	
	def __getattr__(self, attr):
		
		try:
			return self.interfaces[attr]
		except KeyError:
			raise AttributeError("{cls} object has no attribute or interface called {attr}".format(cls=self.__class__.__name__, attr=attr))
	
	def request(self, method, path, data):
		"""
			Makes a request to the API, returning the response as either
			a dictionary (json), ElementTree (xml) or string (VDF) depending
			on specified format.
			
			Should never need to be called directly as calling an
			InterfaceMethod eventually defers to this function.
		"""
		
		if self.format not in ["json", "xml", "vdf"]:
			raise SteamError("Invalid requested format '{}'".format(self.format))
		
		data.update(format=self.format)
		if self.key:
			data.update(key=self.key)
		
		if method.upper() == "POST":
			request = urllib2.Request(
						urlparse.urljoin(self.url, path),
						urllib.urlencode(data)
						)
		elif method.upper() == "GET":
			request = urllib2.Request("{}?{}".format(
										urlparse.urljoin(self.url, path),
										urllib.urlencode(data)))
		
		try:
			response = urllib2.urlopen(request)
		except urllib2.URLError as exc:
			raise SteamError(exc)
		
		if self.format == "json":
			return json.load(response)
		elif self.format == "xml":
			return xml.etree.ElementTree.parse(response)
		else:
			return response.read()
