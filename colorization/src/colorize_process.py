import numpy
import acl
import cv2
import utils
import acl_constants
import os
from model_process import Modelprocess
"""
* Copyright 2020 Huawei Technologies Co., Ltd
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at

* http://www.apache.org/licenses/LICENSE-2.0

* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.

* File sample_process.cpp
* Description: handle acl resource
"""

# constant variables
FAILED = 1
SUCCESS = 0


class ColorizeProcess:

    def __init__(self, modelPath, modelWidth=numpy.uint32(224),
                 modelHeight=numpy.uint32(224),
                 deviceId=0, inputBuf=None, isInit=False, run_mode=0):
        """
        This function does the initiation of variables of colorize process


        Parameters:
        -----------
        modelPath : str
            the model path for colorization (incl. filename)
        modelWidth : numpy.uint32(224)
            the width a image should have, in order to be colorized
        modelHeight : numpy.uint32(224)
            the height a image should have, in order to be colorized
        deviceID : int
            the ID of the device
        inputBuf : int
            pointer to allocated memory
        isInited : boolean
            Ture: the object is inited
            False: the object is not inited yet
        run_mode : int
            the mode of run.
            0: ACL_DEVICE
            1: ACL_HOST

        return value : None
        """

        self.modelPath = modelPath
        self.modelWidth = modelWidth
        self.modelHeight = modelHeight
        self.inputDataSize = 4 * modelWidth * modelHeight
        self.deviceId = deviceId
        self.inputBuf = inputBuf
        self.isInited = isInit
        self.run_mode = run_mode
        self.model = Modelprocess()

    def InitResource(self):
        """
        This function does the initiation of resource.
        Set and get features through acl.


        Parameters:
        -----------
        input : none

        return value : int
            on success this function returns 0
            on failure this function returns 1
        """
        #  ACLCONFIGPATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                     '../acl.json')
        #  ret = acl.init(ACLCONFIGPATH)
        ret = acl.init()  # no configuration.info as argument
        if ret != acl_constants.ACL_ERROR_NONE:
            print("Acl init failed")
            return FAILED
        print("Acl init success")

        # open device
        ret = acl.rt.set_device(self.deviceId)
        if ret != acl_constants.ACL_ERROR_NONE:
            print("Acl open device ", self.deviceId, " failed.")
            return FAILED
        print("Open device ", self.deviceId, " success.")

        (self.run_mode, ret) = acl.rt.get_run_mode()
        if ret != acl_constants.ACL_ERROR_NONE:
            print("acl get_run_mode failed.")
            return FAILED
        return SUCCESS

    def InitModel(self, OMMODELPATH):
        """
        This function does the initiation of model.


        Parameters:
        -----------
        OMMODELPATH : constant str
            the model path for colorization

        return value : int
            on success this function returns 0
            on failure this function returns 1
        """

        ret = self.model.LoadModelFromFileWithMem(OMMODELPATH)
        if ret != SUCCESS:
            print("execute LoadModelFromFileWithMem failed")
            return FAILED

        ret = self.model.CreateDesc()
        if ret != SUCCESS:
            print("execute CreateDesc failed")
            return FAILED
        ret = self.model.CreateOutput()
        if ret != SUCCESS:
            print("execute CreateOutput failed")
            return FAILED

        (self.inputBuf, ret) = acl.rt.malloc(self.inputDataSize,
                                             acl_constants.
                                             ACL_MEM_MALLOC_HUGE_FIRST)
        if self.inputBuf is None:
            print("Acl malloc image buffer failed.")
            return FAILED

        ret = self.model.CreateInput(self.inputBuf, self.inputDataSize)
        if ret != SUCCESS:      # check return value
            print("Create mode input dataset failed")
            return FAILED
        return SUCCESS

    def Init(self):
        """
        This function does the initiation of model.


        Parameters:
        -----------
        input: none

        return value : int
            on success this function returns 0
            on failure this function returns 1
        """

        if self.isInited:
            print("Classify instance is inited already!")
            return SUCCESS

        ret = self.InitResource()
        if ret != SUCCESS:
            print("Init acl resource failed")
            return FAILED

        ret = self.InitModel(self.modelPath)
        if ret != SUCCESS:
            print("Init model failed")
            return FAILED
        self.isInited = True
        return SUCCESS

    def Preprocess(self, imageFile):
        """
        This function reads the imageFile as a float-Matrix;
        downsize to modelWidth*modelHeight;
        if the process run in Atlas, copys the picture data to the device;
        copys the L channel into the malloc memory location.

        Parameters:
        -----------
        input:
        imageFile : str
            the path of the picture

        return value : int
            on success this function returns 0
            on failure this function returns 1
        """
        # read image using OPENCV
        mat = cv2.imread(imageFile, cv2.IMREAD_COLOR).astype(numpy.float32)
        if numpy.any(mat) is None:  # if matrix is empty, every term is none
            return FAILED

        # resize
        reiszeMat = numpy.zeros(self.modelWidth, numpy.float32)

        reiszeMat = cv2.resize(mat, (self.modelWidth, self.modelHeight),
                               cv2.INTER_CUBIC)
        # deal image
        reiszeMat = cv2.convertScaleAbs(reiszeMat, cv2.CV_32FC3)
        reiszeMat = 1.0 * reiszeMat / 255

        # pull out L channel and subtract 50 for mean-centering
        channels = cv2.split(reiszeMat)
        reiszeMatL = channels[0] - 50

        if self.run_mode == 1:
            # if run in AI1, need to copy the picture data to the device
            ret = acl.rt.memcpy(self.inputBuf, self.inputDataSize, reiszeMatL,
                                self.inputDataSize,
                                acl_constants.ACL_MEMCPY_HOST_TO_DEVICE)
            if ret != acl_constants.ACL_ERROR_NONE:  # ACL_ERROR_NONE will be
                # deprecated in future releases.
                # could Use ACL_SUCCESS instead.
                print("Copy resized image data to device failed.")
                return FAILED
            else:
                # 'reiszeMatL' is local variable , cant pass out of function,
                # need to copy it
                acl.rt.memcpy(self.inputBuf, self.inputDataSize, reiszeMatL,
                              self.inputDataSize)

        return SUCCESS

    # Calling the model_process program to do the real colorize process.
    # input: object itself
    # output: pointer value for the result, and the flag SUCCESS or FAILED
    # ATTENTION: THE INPUT AND OUTPUT ARE CHANGED,
    # COMPARE TO THE ORIGINAL C++ CODE!!
    def inference(self):
        """
        This function activate the model process after preprocess,
        and get result back.


        Parameters:
        -----------
        input:none

        return : inferenceOutput, result
        inferenceOutput : int
            pointer of the result saved after colorization
        result : int
            on success this function returns 0
            on failure this function returns 1
        """

        inferenceOutput = None
        ret = self.model.Execute()
        if ret != SUCCESS:
            print("Execute model inference failed")
            return inferenceOutput, FAILED
        inferenceOutput = self.model.GetModelOutputData()
        return inferenceOutput, SUCCESS

    def postprocess(self, input_image_path, output_image_path, modelOutput):
        """This function converts LAB image to BGR image (colorization)
        and save it.
         It combines L channel obtained from source image and ab channels
         from Inference result.

         Parameters:
        -----------
        input_image_path : str
            the path of the (gray) image to obtain L channel
        output_image_path : str
            the path of the (colorized) image to save after processing
        modelOutput : image
            Model output consisting of ab channels.
        return value :
            on success this function returns 0
            on failure this function returns 1
        """
        dataSize = 0
        data = self.GetInferenceOutputItem(dataSize, modelOutput)
        if data is None:
            return FAILED

        # size = int(dataSize)

        # get a and b channel result data

        inference_result = cv2.imread(modelOutput)
        inference_result = cv2.resize(inference_result, (self.modelWidth,
                                                         self.modelHeight))
        ab_channel = inference_result
        # pull out L channel in original/source image

        input_image = cv2.imread(input_image_path, cv2.IMREAD_COLOR)
        input_image = cv2.resize(input_image, (self.modelWidth, self.modelHeight))

        input_image = numpy.float32(input_image)
        input_image = 1.0 * input_image / 255  # Normalizing the
        # input image values
        bgrtolab = cv2.cvtColor(input_image, cv2.COLOR_BGR2LAB)
        cv2.imshow("Lab_channel", bgrtolab)
        (L, A, B) = cv2.split(bgrtolab)
        cv2.imshow("L_channel", L)
        cv2.imshow("A_channel", A)
        cv2.imshow("B_channel", B)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # resize to match the size of original image L

        height = input_image[0]
        width = input_image[1]
        ab_channel_resize = cv2.resize(ab_channel, (height, width))

        # result Lab image

        result_image = cv2.merge(L, ab_channel_resize)
        cv2.imshow('result_image', result_image)

        # convert back to rgb

        output_image = cv2.cvtColor(result_image, cv2.COLOR_Lab2BGR)
        output_image = output_image * 255
        cv2.imshow('output_image', output_image)
        cv2.imwrite(output_image_path, output_image)

        # self.SaveImage(imageFile, output_image)
        return SUCCESS

    def SaveImage(self, origImageFile, image):
        """This function saves the colorized image in a specified path
           Parameters:
           -----------
           origImageFile: str
              the path of original image file
           image: image
              colorized image obtained from postprocess
           returns: None"""
        newpath = os.path.join(origImageFile, "Saved_images")
        os.makedirs(newpath)
        image = cv2.imread(image)
        cv2.imwrite(os.path.join(newpath, "Saved_image.png"), image)  # Saving
        # images
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def GetInferenceOutputItem(self, itemDataSize, inferenceOutput):
        """
        This function obtains the first Buffer of inferenceOutput in dataBuffer;
        obtains the address object of data of the dataBuffer;
        obtains the memory size of data of the dataBuffer in bytes

        Parameters:
        -----------
        input:
        itemDataSize: int
            data size
        inferenceOutput: aclmdlDataset
            pointer of the result saved after colorization

        return value :
        data: int
        the dataset buffer address from model inference output
        """
        dataBuffer = acl.mdl.get_dataset_buffer(inferenceOutput, 0)
        if dataBuffer is None:
            print("Get the dataset buffer from model inference output failed")
            return None

        dataBufferDev = acl.mdl.get_data_buffer_addr(dataBuffer)
        if dataBufferDev is None:
            print(
                "Get the dataset buffer address from model inference output "
                "failed")
            return None

        bufferSize = acl.mdl.get_data_buffer_size(dataBuffer)
        if bufferSize == 0:
            print("The dataset buffer size of model inference output is 0 ")
            return None
        data = None
        if self.run_mode == acl_constants.ACL_HOST:
            data = utils.CopyDataDeviceToHost(dataBufferDev, bufferSize)
            if data is None:
                print("Copy inference output to host failed")
                return None
        else:
            data = dataBufferDev

        # itemDataSize = bufferSize
        return data

    def DestroyResource(self):
        """
        This function uninstalls the model and releases resources after the
        model inference is complete; destroys data of the aclmdlDesc type;
        destroys input and output data; resets the computing device and
        releases the resources (including the default context and stream,
        and all streams created in the default context) on the device;
        deinitializes ACL before the application processends;
        frees the memory on the device allocated by acl.rt.malloc.


        Parameters:
        -----------
        input:
        self: class ColorizeProcess

        return value :
        None
        """
        self.model.Unload(self)
        self.model.DestroyDesc(self)
        self.model.DestroyInput(self)
        self.model.DestroyOutput(self)

        ret = acl.rt.reset_device(self.deviceId)
        if ret != acl_constants.ACL_ERROR_NONE:
            print("reset device failed")

        print("end to reset device is %d", self.deviceId)

        ret = acl.finalize()
        if ret != acl_constants.ACL_ERROR_NONE:
            print("finalize acl failed")

        print("end to finalize acl")
        acl.rt.free(self.inputBuf)
        self.inputBuf = None
