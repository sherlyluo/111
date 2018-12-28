import os
import sys
import urllib
import urllib2
import urlparse
from HTMLParser import HTMLParser


class Product():
	"""Bounds product"""
	def __init__(self):
		self.name = ''
		self.price = ''
		self.swatches = []
		self.images = []

class BondsSwatchProductImageConverter():
	"""
	Convert swatch url (https://media.bonds.com.au/catalog/product/cache/1/colour_swatch/9df78eab33525d08d6e5fb8d27136e95/B/Y/BYEXA_4MG.png)
	to product image url (https://media.bonds.com.au/catalog/product/cache/1/image/800x1200/9df78eab33525d08d6e5fb8d27136e95/B/Y/BYEXA_4MG_1.jpg)
	"""
	def __init__(self):
		self.images = []

	def convert(self, swatchlist):
		swatch_url_prefix = 'https://media.bonds.com.au/catalog/product/cache/1/colour_swatch/'
		swatch_url_postfix = '.png'

		product_url_prefix = 'https://media.bonds.com.au/catalog/product/cache/1/image/800x1200/'
		product_url_postfix = '_1.jpg'
		for url in swatchlist:
			product_url = url.replace(swatch_url_prefix, product_url_prefix).replace(swatch_url_postfix, product_url_postfix)

			self.images.append(product_url)

		return self.images

class BondsProductParser(HTMLParser):
	"""
	Parse Bonds product page https://www.bonds.com.au/zip-wondersuit-bzbva-8jf.html
	to an product info
	"""
	def __init__(self):
		HTMLParser.__init__(self)

		self.swatch_urls = []
		self.product = Product()
		self.isname = False
		self.isprice = False

	def handle_starttag(self, tag, attrs):
		if tag.lower() == 'h1':
			for name, value in attrs:
				if name == 'itemprop' and value == 'name':
					self.isname = True

		if tag.lower() == 'span':
			pricetag = False
			newprice = False
			for name, value in attrs:
				if name == 'class' and value == 'price':
					pricetag = True
				if name == 'id' and value.startswith('product-price'):
					newprice = True
			self.isprice = pricetag and newprice

		if tag.lower() == 'img':
			for name, value in attrs:
				if name == 'data-src':
					if value.endswith('.png'):
						'''print value'''
						self.product.swatches.append(value)

	def handle_data(self, data):
		if self.isname:
			self.product.name = data.strip()
			self.isname = False

		if self.isprice:
			self.product.price = data.strip()
			self.isprice = False

	def result(self):
		if len(self.product.images) == 0:
			self.product.images = BondsSwatchProductImageConverter().convert(self.product.swatches)
		return self.product

class BoundsProductDownloader():
	def __init__(self):
		self.product_urls = []

	def run(self):
		if len(self.product_urls) == 0:
			print "No data in the product url file"
			return

		for product_url in self.product_urls:
			print 'Parsing product in ' + product_url

			html = ''
			try:
				request = urllib2.Request(product_url)
				html = urllib2.urlopen(request).read()
			except Exception as e:
				print 'Request product url error, skip.'
				continue

			parser = BondsProductParser()
			parser.feed(html)
			product = parser.result()
			print 'Product parsed, name: {}, price: {}, image count: {}'.format(product.name, product.price, len(product.images))

			directory = self._createproductfolder(product.name)
			self._download(directory, product.images)

	def setsource(self, urls):
		self.product_urls = urls

	def _createproductfolder(self, str):
		"""
		Create folder named str, if not exited
		"""
		current_directory = os.getcwd()
		expected_dir = str.replace(' ', '_')
		final_directory = os.path.join(current_directory, expected_dir)
		if not os.path.exists(final_directory):
			print 'Creating folder: ' + expected_dir + "in: " + current_directory
			os.makedirs(final_directory)

		return final_directory

	def _download(self, dir, urls):
		for url in urls:
			urlpath = urlparse.urlparse(url)
			print 'Downloading: ' + url + '...',
			file = os.path.join(dir, os.path.basename(urlpath.path))
			if os.path.exists(file):
				print 'Exists, skip.'
				continue
			try:
				urllib.urlretrieve(url, file)
			except Exception as e:
				print 'Download error, skip.'
				continue
			print 'Done.'

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print 'Expected source file in arg'
		exit()

	source_file = sys.argv[1]
	if not os.path.exists(source_file):
		print 'Source file does not existed'
		exit()

	f = open(source_file, 'r')
	product_urls = f.readlines()

	downloader = BoundsProductDownloader()
	downloader.setsource(product_urls)
	downloader.run()
