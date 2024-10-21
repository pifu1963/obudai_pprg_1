import pydicom as dicom
import os
import numpy as np


class LoadVolumes:
    """
    This is the sample class to load DICOM - mostly written by Mediso - files into the system.

    This method has the same implementation as the 2D version

    Loads all types of different source DICOM files into the system in the (z,y,x) order. The result is 
    a numeric tensor with the previously defined axis ordering in the text.

    TODO: It will need some update to correctly read all the Mediso DICOM tags and informations to handle
    quantitative calculations.

    TODO: Handle the reading the data from a variable in memory when we do load data from the server itself  
    """

    folder_path = ''
    """This is the member of holding the root folder path (absolute)"""

    volume = []
    """This is the data extracted from the DICOM files"""

    dims = [0, 0, 0]
    """Dimensions of the data that has been loaded from the DICOM file"""

    const_pixel_spacing = [0, 0, 0]
    """Member holding the size of the uniform pixel spacing"""

    dcm_dataset = None

    def __init__(self):
        pass

    def Load(self):
        """
        Loads all the dicom files in a folder to the member volume
        
        
        Parameters
        ----------
        self : None            

        Returns
        -------
        self : None
        
        Notes
        -----
        Written by Adam Istvan Szucs, January 2022.        

        See also
        --------
        data
        """

        dicom_file_list = []

        for dirName, subdirList, fileList in os.walk(self.folder_path):
            for filename in fileList:
                if ".dcm" in filename.lower():
                    dicom_file_list.append(os.path.join(dirName, filename))

        RefDs = dicom.read_file(dicom_file_list[0])

        const_pixel_dims = (int(RefDs.Rows), int(RefDs.Columns), len(dicom_file_list))
        const_pixel_spacing = (float(RefDs.PixelSpacing[0]), float(RefDs.PixelSpacing[1]), float(RefDs.SliceThickness))

        self.dims = const_pixel_dims
        self.const_pixel_spacing = const_pixel_spacing

        x = np.arange(0.0, (const_pixel_dims[0] + 1) * const_pixel_spacing[0], const_pixel_spacing[0])
        y = np.arange(0.0, (const_pixel_dims[1] + 1) * const_pixel_spacing[1], const_pixel_spacing[1])
        z = np.arange(0.0, (const_pixel_dims[2] + 1) * const_pixel_spacing[2], const_pixel_spacing[2])

        self.volume = np.zeros(const_pixel_dims, dtype=RefDs.pixel_array.dtype)

        for dicom_file_name in dicom_file_list:
            ds = dicom.read_file(dicom_file_name)
            self.volume[:, :, dicom_file_list.index(dicom_file_name)] = ds.pixel_array

    def LoadSinglePatient(self, a_dicom_file_name):
        """
        Loads all the dicom files in a folder to the member volume
        
        
        Parameters
        ----------
        self : None
        a_dicom_file_name : str 
                            Absolute path for the dicom file that the user wants to load.

        Returns
        -------
        volume : (N, M, K[, 1]) ndarray 
                 A tensor containing the scalar field of various dimension
        
        Notes
        -----
        Written by Adam Istvan Szucs, January 2022.        

        See also
        --------
        data
        """
        self.dcm_dataset = dicom.read_file(a_dicom_file_name)
        dcm_dataset = self.dcm_dataset

        const_pixel_dims = np.zeros([0, 0, 0])
        const_pixel_spacing = np.zeros([0, 0, 0])

        if hasattr(dcm_dataset, 'NumberOfSlices'):
            const_pixel_dims = (
                int(dcm_dataset.NumberOfSlices), int(dcm_dataset.Rows), int(dcm_dataset.Columns))
            const_pixel_spacing = (float(dcm_dataset.PixelSpacing[0]), float(dcm_dataset.PixelSpacing[1]),
                                   float(dcm_dataset.SliceThickness))
        else:
            const_pixel_dims = (
                int(dcm_dataset.NumberOfFrames), int(dcm_dataset.Rows), int(dcm_dataset.Columns))
            const_pixel_spacing = (float(dcm_dataset.PixelSpacing[0]), float(dcm_dataset.PixelSpacing[1]),
                                   float(1))

        self.dims = const_pixel_dims
        self.const_pixel_spacing = const_pixel_spacing

        self.volume = np.zeros(const_pixel_dims, dtype=np.float64)

        self.volume[:, :, :] = dcm_dataset.pixel_array

        return self.volume[:, :, :], True

    def CalculatePatientStatistics(self):
        dcm_dataset = self.dcm_dataset

        if hasattr(dcm_dataset, 'PatientWeight'):
            weight = dcm_dataset.get_item('PatientWeight').value
        else:
            weight = 0.0

        if hasattr(dcm_dataset, 'PatientSex'):
            gender = dcm_dataset.get_item('PatientSex').value
        else:
            gender = 'U'

        if hasattr(dcm_dataset, 'PatientSize'):
            height = dcm_dataset.get_item('PatientSize').value
        else:
            height = 0.0

        if hasattr(dcm_dataset, 'PatientSize'):
            from datetime import date
            birthdate_num = dcm_dataset.get_item('PatientBirthDate').value

            if len(birthdate_num) > 0:
                birthdate = date(int(birthdate_num[0:4]), int(birthdate_num[4:6]), int(birthdate_num[6:8]))
                def calculate_age(born):
                    today = date.today()
                    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

                age = calculate_age(birthdate)
            else:
                age = 0.0
        else:
            age = 0.0

        return float(age), gender, float(weight), float(height)
