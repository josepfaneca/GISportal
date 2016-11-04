import math
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
import netCDF4
from data_extractor.extraction_utils import WCSRawHelper
from . import Extractor


class TransectExtractor(Extractor):
   """docstring for TransectExtractor"""

   thredds_max_request = 4000

   def __init__(self, wcs_url, extract_dates, transect_type, extract_area=None, extract_variable=None, extract_depth=None):
      super(TransectExtractor, self).__init__(wcs_url, extract_dates, extract_area=extract_area, extract_variable=extract_variable,  extract_depth=extract_depth)

   def getData(self):
      coverage_description = self.getCoverageDescriptionData()
      max_slices = self.getMaxSlices(coverage_description['offset_vectors'])
      slices_in_range = self.getSlicesInRange(coverage_description['time_slices'])

      files = self.getFiles(slices_in_range, max_slices)

      # if len(files) > 1:
      #  fname = self.mergeFiles(files)
      # else:
      #  fname = files[0]

      return files

   def getFiles(self, slices_in_range, max_slices):
      # if len(slices_in_range) < max_slices:
      #  data = wcs_extractor.getData()
      #  fname = self.outdir+str(uuid.uuid4())+".nc"
      #  with open(fname, 'w') as outfile:
      #     outfile.write(data.read())
      # else:

      files = []
      next_start = 0
      for _ in range(0, int(math.ceil(len(slices_in_range) / float(max_slices)))):
         start = slices_in_range[next_start].strftime('%Y-%m-%d %H:%M:%S')
         if next_start + max_slices < len(slices_in_range):
            end_index = next_start + max_slices
         else:
            end_index = len(slices_in_range) - 1
         end = slices_in_range[end_index].strftime('%Y-%m-%d %H:%M:%S')
         next_start = next_start + max_slices + 1
         extract_dates = start + '/' + end

         wcs_extractor = WCSRawHelper(self.wcs_url, extract_dates, self.extract_variable, self.extract_area, self.extract_depth)
         data = wcs_extractor.getData()

         fname = self.outdir + str(uuid.uuid4()) + ".nc"

         # Download in 16K chunks. This is most efficient for speed and RAM usage.
         chunk_size = 16 * 1024
         with open(fname, 'w') as outfile:
            while True:
               chunk = data.read(chunk_size)
               if not chunk:
                  break
               outfile.write(chunk)
         files.append(fname)
      return files

   def getMaxSlices(self, offset_vectors):
      area_width = self.extract_area[3] - self.extract_area[1]
      area_height = self.extract_area[2] - self.extract_area[0]

      pixel_width = abs(area_width / offset_vectors['x'])
      pixel_height = abs(area_height / offset_vectors['y'])

      pixel_area = pixel_width * pixel_height

      slice_bytes = pixel_area * 4
      slice_megabytes = slice_bytes / 1024 / 1024

      max_slices = int(self.thredds_max_request / slice_megabytes)

      return max_slices

   def getSlicesInRange(self, time_slices):
      date_range = '/'.join(self.extract_dates).split('/')

      for i, date in enumerate(date_range):
         date_range[i] = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

      slices_in_range = []
      for time_slice in time_slices:
         time_slice = datetime.strptime(time_slice, '%Y-%m-%dT%H:%M:%SZ')
         if time_slice >= date_range[0] and time_slice <= date_range[1]:
            slices_in_range.append(time_slice)

      return slices_in_range

   def getCoverageDescriptionData(self):
      coverage_description = {}
      ns = {'xmlns': 'http://www.opengis.net/wcs', 'gml': 'http://www.opengis.net/gml', 'xlink': 'http://www.w3.org/1999/xlink'}
      wcs_extractor = WCSRawHelper(self.wcs_url, self.extract_dates, self.extract_variable, self.extract_area, self.extract_depth)
      coverage_description_xml = ET.fromstring(wcs_extractor.describeCoverage())

      rectified_grid = coverage_description_xml.find('./xmlns:CoverageOffering/xmlns:domainSet/xmlns:spatialDomain/gml:RectifiedGrid', ns)
      axis_names = []
      for axis_name in rectified_grid.findall('./gml:axisName', ns):
         axis_names.append(axis_name.text)

      coverage_description['offset_vectors'] = {}
      i = 0
      for offset_vector in rectified_grid.findall('./gml:offsetVector', ns):
         for item in offset_vector.text.split(' '):
            if float(item) != 0:
               coverage_description['offset_vectors'][axis_names[i]] = float(item)
               i += 1

      # time_slices =
      coverage_description['time_slices'] = []
      for time_slice in coverage_description_xml.findall('./xmlns:CoverageOffering/xmlns:domainSet/xmlns:temporalDomain/gml:timePosition', ns):
         coverage_description['time_slices'].append(time_slice.text)

      return coverage_description

   def mergeFiles(self, files):
      # Create new file
      fname = self.outdir + str(uuid.uuid4()) + ".nc"
      # new_file = netCDF4.Dataset(fname, 'w', format='NETCDF3_64BIT')
      new_file = netCDF4.Dataset(fname, 'w', format='NETCDF4')
      # Load first downloaded file
      first_file = netCDF4.Dataset(files[0], 'r')
      # Copy attrs from first file into new file
      for attr in first_file.ncattrs():
         new_file.setncattr(attr, first_file.getncattr(attr))

      # Create dimensions and variables in new file
      new_file.createDimension('time', None)
      # new_file.createDimension('lat', None)
      new_file.createDimension('lat', len(first_file.dimensions['lat']))
      # new_file.createDimension('lon', None)
      new_file.createDimension('lon', len(first_file.dimensions['lon']))

      time = new_file.createVariable('time', first_file.variables['time'].dtype, ('time',), zlib=False)
      lat = new_file.createVariable('lat', first_file.variables['lat'].dtype, ('lat',), zlib=False)
      lon = new_file.createVariable('lon', first_file.variables['lon'].dtype, ('lon',), zlib=False)
      variable = new_file.createVariable(self.extract_variable, first_file.variables[self.extract_variable].dtype, ('time', 'lat', 'lon'), zlib=False)

      # Copy variable attrs from first file variables to new file variables
      ignored_attr = ['size', 'shape']
      for attr in first_file.variables['time'].ncattrs():
         if attr not in ignored_attr:
            time.setncattr(attr, first_file.variables['time'].getncattr(attr))

      for attr in first_file.variables['lat'].ncattrs():
         if attr not in ignored_attr:
            lat.setncattr(attr, first_file.variables['lat'].getncattr(attr))

      for attr in first_file.variables['lon'].ncattrs():
         if attr not in ignored_attr:
            lon.setncattr(attr, first_file.variables['lon'].getncattr(attr))

      for attr in first_file.variables[self.extract_variable].ncattrs():
         if attr not in ignored_attr:
            variable.setncattr(attr, first_file.variables[self.extract_variable].getncattr(attr))

      new_lat = first_file.variables['lat']
      new_lon = first_file.variables['lon']
      start = 0
      end = len(new_lat)
      lat[start:end] = new_lat

      end = len(new_lon)
      lon[start:end] = new_lon

      first_file.close()

      for _file in files:
         f = netCDF4.Dataset(_file, 'r')
         new_time = f.variables['time']
         new_variable = f.variables[self.extract_variable]

         start = len(time)
         end = start + len(new_time)

         time[start:end] = new_time
         variable[start:end] = new_variable

         f.close()

      new_file.close()

      return fname
