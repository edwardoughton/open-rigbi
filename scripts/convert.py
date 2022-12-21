"""

"""
import os
import configparser
import glob

from misc import remove_small_shapes

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def convert_surface_water_to_shapes():
    """

    """
    import os, gdal

    input_folder = os.path.join(DATA_RAW, 'global_surface_water')
    paths = glob.glob(os.path.join(input_folder, "*.tif"))#[100:102]

    for path_in in paths:

        input_filename = os.path.basename(path_in)

        # if not input_filename in [
        #     'occurrence_20E_0Nv1_3_2020.tif',
        #     'occurrence_30E_0Nv1_3_2020.tif'
        #     ]:
        #     continue

        output_folder = os.path.join(DATA_RAW, 'global_surface_water', 'chopped')
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        tile_size_x = 25000
        tile_size_y = 25000

        try:
            path_in = os.path.join(input_folder, input_filename)

            ds = gdal.Open(os.path.join(input_folder, input_filename))

            band = ds.GetRasterBand(1)

            xsize = band.XSize
            ysize = band.YSize

            for i in range(0, xsize, tile_size_x):

                for j in range(0, ysize, tile_size_y):

                    output_filename = '{}_{}_{}.tif'.format(
                        os.path.basename(path_in)[:-4], i, j
                    )

                    path_out = os.path.join(output_folder, output_filename)

                    if os.path.exists(path_out):
                        continue

                    com_string = (
                        "gdal_translate -of GTIFF -srcwin " + str(i)+ ", " + str(j) + ", " +
                        str(tile_size_x) + ", " + str(tile_size_y) + " " + path_in + " " +
                        path_out + ' -co compress=LZW'
                    )

                    os.system(com_string)
        except:
            continue


if __name__ == "__main__":

    convert_surface_water_to_shapes()
