# coding=utf-8
# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS IS."
#  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES, OFFICERS,
#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO THE USEFULNESS
#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE. THEY ASSUME NO RESPONSIBILITY
#  (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL
#  SUPPORT TO USERS.

"""


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np

class ping_data(object):
    """
    echolab2.ping_data is the base class for all classes that store "ping"
    based data from fisheries sonar systems.  This class is not intended to be
    instantiated by the user. It is a base class that defines the common data
    attributes and methods that the user facing classes share.

    Derived classes will add various attributes to this class that store
    either scalar values on a per-ping basis like sound velocity, transmit power
    transducer depth, etc. or attributes that store vector data such as
    sample power and sample angle data.

    One major assumption is that all data stored within an instance of our
    derived classes must exist on the same "time grid". It is assumed that the
    index of a specific ping time should map to other attributes collected at
    that time. As a result, all attributes should share the same primary dimension.
    """

    def __init__(self):

        #  all data classes contain the following attribites

        #  n_pings stores the total number of pings contained in our container
        self.n_pings = -1

        #  the number of samples in the 2d sample arrays
        self.n_samples = -1

        #  allow the user to specify a dtype for the sample data. This should be set before
        #  any attributes are added.
        self.sample_dtype = 'float32'

        #  _data_attributes is an internal list that contains the names of all of the class's
        #  "data attributes". The echolab2 package uses this attribute to generalize various
        #  functions that manipulate these data.
        #
        #  "data attributes" are attributes that store data by ping. They can be 1d such as
        #  ping_time, sample_interval, and transducer_depth. Or they can be 2d such as power,
        #  Sv, angle data, etc. echolab2 supports attributes that are 1 and 2d numpy
        #  arrays. When subclassing, you must extend this list in your __init__ method
        #  to contain all of the data attributes of that class that you want to exist at
        #  instantiation (attributes can also be added later.)

        #  for the base class, we only define ping_time which is the only required attribute
        #  that all data objects must have.
        self._data_attributes = ['ping_time']

        #  attributes are added using the add_attribute method. You can add them manually
        #  by appending the name of the new attribute to the _data_attributes dict and
        #  then setting the attribute using setattr().

        #  when writing methods that operate on these data, we will not assume that they
        #  exist. An attribute should only exist if it contains data.


    def add_attribute(self, name, data):
        """
        add_attribute adds a "data attribute" to the class. It first checks if the new
        attribute shares the same dimensions as existing attributes and if so appends the
        attribute name to our internal list of data attributes and then creates an
        attribute by that name and sets it to the provided reference.
        """

        #  get the new data's dimensions
        data_height = -1
        if (isinstance(data, np.ndarray)):
            if (data.ndim == 1):
                data_width = data.shape[0]
            if (data.ndim == 2):
                data_width = data.shape[0]
                data_height = data.shape[1]
                #  check if n_samples has been set yet. If not, set it. If so, check that dimensions match
                if (self.n_samples < 0):
                    self.n_samples = data_height
                elif (self.n_samples != data_height):
                    #TODO:  Better error message
                    raise ValueError('Cannot add attribute. New attribute has a different ' +
                            'number of samples than the other attributes.')
        else:
            #  we only allow numpy arays as data attributes
            raise TypeError('Invalid data attribute type. Data attributes must be numpy arrays.')

        #  check if n_pings has been set yet. If not, set it. If so, check that dimensions match
        #  when checking if dimensions match we allow a match on the number of pings OR the number
        #  of the samples since a 1d data attribute can be on either axis.
        if (self.n_pings < 0):
            self.n_pings = data_width
        elif (self.n_pings != data_width and self.n_samples != data_width):
            #TODO:  Better error message
            raise ValueError('Cannot add attribute as the new attribute has a different ' +
                    'number of pings (or samples) than the other attributes.')

        #  add the name to our list of attributes if it doesn't already exist
        if (name not in self._data_attributes):
            self._data_attributes.append(name)

        #  and add it to self
        setattr(self, name, data)


    def remove_attribute(self, name):
        """
        remove_attribute removes a data attribute from the object.
        """

        #  try to remove the attribute given the name. Silently fail if name is not in our list
        try:
            self._data_attributes.remove(name)
            delattr(self, name)
        except:
            pass


    def replace(self, obj_to_insert, ping_number=None, ping_time=None,
               index_array=None, _ignore_vertical_axes=False):
        """
        replace, er, replaces the data in this object using the data provided
        in the obejct to "insert". Another way to think of this is that it
        inserts data without shifting the existing data resulting in the
        existing data being overwritten.

        Args:
            ping_number: The ping number specifying the first ping to replace
            ping_time: The ping time specifying the first ping to replace
            index_array: A numpy array containing the indices of the pings you
                want to replace. Unlike when using a ping number or ping time,
                the pings do not have to be consecutive. When this keyword is
                present, the ping_number and ping_time keywords are ignored.

        You must specify a ping number, ping time or provide an index array.
        The number of pings replaced will be equal to the number of pings in
        the object you are

        """

        #  check that we have been given an insetion point or index array
        if ping_number is None and ping_time is None and index_array is None:
            raise ValueError('Either ping_number or ping_time needs to be defined ' +
                    'or an index array needs to be provided to specify an replacement point.')

        #  make sure that obj_to_insert class matches "this" class
        if (not isinstance(self, obj_to_insert.__class__)):
            raise TypeError('The object provided as a source of replacement pings must ' +
                    'be an instance of ' + str(self.__class__))

        #  make sure that the frequencies match - don't allow replacing pings with different freqs
        freq_match = False
        if isinstance(self.frequency, np.float32):
            freq_match = self.frequency == obj_to_insert.frequency
        else:
            freq_match = self.frequency[0] == obj_to_insert.frequency[0]
        if (not freq_match):
            raise TypeError('The frequency of the data you are providing as a replacement ' +
                    'does not match the frequency of this object. The frequencies must match.')

        #  get some info about the shape of the data we're working with
        my_pings = self.n_pings
        new_pings = obj_to_insert.n_pings
        my_samples = self.n_samples
        new_samples = obj_to_insert.n_samples

        #  determine the index of the replacement point or indices of the pings we're inserting.
        if (index_array is None):
            #  determine the index of the replacement point
            replace_index  = self.get_indices(start_time=ping_time, end_time=ping_time,
                    start_ping=ping_number, end_ping=ping_number)[0]

            #  create an index array
            replace_index = np.arange(new_pings) + replace_index

            #  clamp the index to the length of our existing data.
            replace_index = replace_index[replace_index <  my_pings]

        else:
            #  explicit array provided - these will be a vector of locations to replace
            replace_index  = index_array

            #  make sure the index array is a numpy array
            if (not isinstance(replace_index, np.ndarray)):
                raise TypeError('index_array must be a numpy.ndarray.')

            #  If we replacing with a user provided index, make sure the dimensions of the
            #  index and the object to insert agree.
            if (replace_index.shape[0] != new_pings):
                raise IndexError('The length of the index_array does not match the ' +
                        'number of pings in the object providing the replacement data. ' +
                        'These dimensions must match.')

        #  check if we need to vertically resize one of the arrays - we resize the smaller to
        #  the size of the larger array. It will automatically be padded with NaNs
        if (my_samples < new_samples):
            #  resize our data arrays - check if we have a limit on the max number of samples
            if (hasattr(self, 'max_sample_number') and (self.max_sample_number)):
                #  we have the attribute and a value is set - check if the new array exceeds our max_sample_count
                if (new_samples > self.max_sample_number):
                    #  it does - we have to change our new_samples
                    new_samples = self.max_sample_number
                    #  and vertically trim the array we're inserting
                    obj_to_insert.resize(new_pings, new_samples)
            #  because we're not inserting, we can set the new vertical sample size here
            self.resize(my_pings, new_samples)
        elif (my_samples > new_samples):
            #  resize the object we're inserting
            obj_to_insert.resize(new_pings, my_samples)

        #  work thru our data properties inserting the data from obj_to_insert
        for attribute in self._data_attributes:

            #  check if we have data for this attribute
            if (not hasattr(self, attribute)):
                #  data_obj does not have this attribute, move along
                continue

            #  get a reference to our data_obj's attribute
            data = getattr(self, attribute)

            #  check if we're ignoring vertical axes such as range or depth
            #  we do this when operating on processed data objects since the
            #  assumption with them is that the
            if (_ignore_vertical_axes and (data.shape[0] == my_samples)):
                continue

            #  check if the obj_to_insert shares this attribute
            if (hasattr(obj_to_insert, attribute)):
                #  get a reference to our obj_to_insert's attribute
                data_to_insert = getattr(obj_to_insert, attribute)

                #  we have to handle the 2d and 1d differently
                if (data.ndim == 1):
                    #  concatenate the 1d data - replace existing pings with this data
                    data[replace_index] = data_to_insert[:]
                elif (data.ndim == 2):
                    #  and insert the new data
                    data[replace_index, :] = data_to_insert[:,:]

                else:
                    #  at some point do we handle 3d arrays?
                    pass

        #  now update our global properties
        if (obj_to_insert.channel_id not in self.channel_id):
            self.channel_id += obj_to_insert.channel_id


    def delete(self, start_ping=None, end_ping=None, start_time=None,
               end_time=None, remove=True, index_array=None):
        """
        delete deletes data from an echolab2 data object by ping over the range
        defined by the start and end pings/times. If remove is True, the data
        arrays are shrunk, if False the arrays stay the same size and the data
        values are set to NaNs (or appropriate value based on type)

        Args:
            start_ping: The starting ping of the range of pings to delete
            end_ping: The ending ping of the range of pings to delete
            start_time: The starting time of the range of pings to delete
            end_time: The ending time of the range of pings to delete

                You should set only one start and end point.

            remove: Set to True to remove the specified pings and shrink the
                data arrays. When set to false, data in the deleted pings are
                set to Nan (or appropriate value for the data type.)
            index_array: A numpy array containing the indices of the pings you
                want to delete. Unlike when using starts/ends to define the
                ping range to delete, the pings do not have to be consecutive.
                When this keyword is present, the start/end keywords are ignored.

        """
        #  determine the indices of the pings we're deleting.
        if (index_array is None):
            #  if we haven't been provided an explicit array, create one based on provided ranges
            del_idx = self.get_indices(start_time=start_time, end_time=end_time,
                                       start_ping=start_ping, end_ping=end_ping)
        else:
            #  explicit array provided
            del_idx = index_array

        #  determine the indices of the pings we're keeping
        keep_idx = np.delete(np.arange(self.ping_time.shape[0]), del_idx)

        #  and the number of pings we're keeping
        new_n_pings = keep_idx.shape[0]

        #  work thru the attributes to delete the data - if we're removing
        # the pings we first copy the data we're keeping to a contiguous
        # block before we resize all of the arrays (which will shrink them.)
        # If we're not removing the pings, we simply set the values of the
        # various attributes we're deleting to NaNs.
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if isinstance(attr, np.ndarray) and (attr.ndim == 2):
                if remove:
                    attr[0:new_n_pings, :] = attr[keep_idx, :]
                else:
                    attr[del_idx, :] = np.nan
            else:
                if remove:
                        #  copy the data we're keeping into a contiguous block
                        attr[0:new_n_pings] = attr[keep_idx]
                else:
                    # set the data to NaN or apprpriate value
                    if (attr.dtype in [np.float16, np.float32, np.float64, np.datetime64]):
                        #  float like objects are set to NaN == NaT for datetime64
                        attr[del_idx] = np.nan
                    elif (attr.dtype in [np.uint16, np.uint32, np.uint64, np.uint8]):
                        #  unsigned ints are set... well, what really is an appropriate value???
                        attr[del_idx] = 0
                    else:
                        #  and signed ints... -1? -999? -9999? it's a good question.
                        attr[del_idx] = -1

        #  if we're removing the pings, resize (shrink) the arrays
        if (remove):
            self.resize(new_n_pings, self.n_samples)

        #  update the n_pings attribute
        self.n_pings = self.ping_time.shape[0]


    def append(self, obj_to_append):
        """
        append appends another echolab2 data object to this one. The objects must
        be instances of the same class and share the same frequency.
        """

        #  append simply inserts at the end of our internal array.
        self.insert(obj_to_append, ping_number=self.n_pings)


    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               insert_after=True, index_array=None):
        """
        insert inserts the data from the provided echolab2 data object into
        this object. The insertion point is specified by ping number or time.
        After inserting data, the ping_number property is updated and the
        ping numbers will be re-numbered accordingly.

        Args:
            ping_number: The ping number specifying the insertion point
            ping_time: The ping time specifying the insertion point

            You must specify a ping number or ping time. Existing data from
            the insertion point on will be shifted after the inserted data.

            insert_after: Set to True to insert *after* the specified ping time
                or ping number. Set to False to insert *at* the specified time
                or ping number.

            index_array: A numpy array containing the indices of the pings you
                want to insert. Unlike when using a ping number or ping time,
                the pings do not have to be consecutive. When this keyword is
                present, the ping_number, ping_time and insert_after keywords
                are ignored.

        """

        #  check that we have been given an insetion point or index array
        if ping_number is None and ping_time is None and index_array is None:
            raise ValueError('Either ping_number or ping_time needs to be ' +
                             'defined or an index array needs to be provided ' +
                             'to specify an insertion point.')

        #  make sure that obj_to_insert class matches "this" class
        if (not isinstance(self, obj_to_insert.__class__)):
            raise TypeError('The object you are inserting/appending must ' +
                            'be an instance of ' + str(self.__class__))

        #  make sure that the frequencies match - don't allow inserting/appending of
        #  different freqs. We allow NaNs because we allow empty data to be inserted.
        freq_match = False
        if isinstance(self.frequency, np.float32):
            if (obj_to_insert.frequency == np.nan):
                freq_match = True
            else:
                freq_match = self.frequency == obj_to_insert.frequency
        else:
            #  we get lazy with vectors of frequency since there isn't a simple solution.
            if (np.isnan(obj_to_insert.frequency[0])):
                freq_match = True
            else:
                freq_match = self.frequency[0] == obj_to_insert.frequency[0]
        if (not freq_match):
            raise TypeError('The frequency of the object you are inserting' +
                            '/appending does not match the frequency of this ' +
                            'object. Frequencies must match to append or ' +
                            'insert.')

        #  get some info about the shape of the data we're working with
        my_pings = self.n_pings
        new_pings = obj_to_insert.n_pings
        my_samples = self.n_samples
        new_samples = obj_to_insert.n_samples

        #  determine the index of the insertion point or indices of the pings
        #  we're inserting.
        if (index_array is None):
            #  determine the index of the insertion point
            insert_index = self.get_indices(start_time=ping_time,
                                            end_time=ping_time,
                                            start_ping=ping_number,
                                            end_ping=ping_number)[0]

            # check if we're inserting before or after the provided insert
            # point and adjust as necessary
            if (insert_after):
                #  we're inserting *after* - increment the index by 1
                insert_index += 1

            #  create an index array
            insert_index = np.arange(new_pings) + insert_index

            #  generate the index used to move the existing pings
            move_index = np.arange(my_pings)
            idx = move_index >= insert_index[0]
            move_index[idx] = move_index[idx] + new_pings

        else:
            #  explicit array provided - these will be a vector of locations to insert
            insert_index = index_array

            #  make sure the index array is a numpy array
            if (not isinstance(insert_index, np.ndarray)):
                raise TypeError('index_array must be a numpy.ndarray.')

            #  If we are inserting with a user provided index, make sure the
            #  dimensions of the index and the object to insert agree
            if (insert_index.shape[0] != new_pings):
                raise IndexError('The length of the index_array does not ' +
                                 'match the number of pings in the object' +
                                 ' you are inserting.')

            #  generate the index used to move the existing pings
            move_index = np.arange(my_pings)
            print(my_pings, move_index)
            for i in insert_index:
                idx = move_index >= i
                move_index[idx] = move_index[idx] + 1

        #  check if we need to vertically resize one of the arrays - we
        #  resize the smaller to the size of the larger array. It will
        #  automatically be padded with NaNs
        if (my_samples < new_samples):
            #  resize our data arrays - check if we have a limit on the
            #  max number of samples
            if (hasattr(self, 'max_sample_number') and (self.max_sample_number)):
                #  we have the attribute and a value is set - check if the
                #  new array exceeds our max_sample_count
                if (new_samples > self.max_sample_number):
                    #  it does - we have to change our new_samples
                    new_samples = self.max_sample_number
                    #  and vertically trim the array we're inserting
                    obj_to_insert.resize(new_pings, new_samples)
            #  set the new vertical sample size
            my_samples = new_samples
        elif (my_samples > new_samples):
            #  resize the object we're inserting
            obj_to_insert.resize(new_pings, my_samples)

        #  update the number of pings in the object we're inserting into
        #  and then resize it.
        my_pings = my_pings + new_pings
        self.resize(my_pings, my_samples)

        #  work thru our data properties inserting the data from obj_to_insert
        for attribute in self._data_attributes:

            #  check if we have data for this attribute
            if (not hasattr(self, attribute)):
                #  data_obj does not have this attribute, move along
                continue

            #  get a reference to our data_obj's attribute
            data = getattr(self, attribute)

            #  generate the move index
            move_idx = np.arange(move_index.shape[0])

            #  check if the obj_to_insert shares this attribute
            if (hasattr(obj_to_insert, attribute)):
                #  get a reference to our obj_to_insert's attribute
                data_to_insert = getattr(obj_to_insert, attribute)

                #  we have to handle the 2d and 1d differently
                if (data.ndim == 1 and data.shape[0] != my_samples):
                    #  skip vertical axis attributes but move the other 1d data
                    #  move right to left to avoid overwriting data before moving
                    data[move_index[::-1],] = data[move_idx[::-1]]
                    #  and insert the new data
                    data[insert_index] = data_to_insert[:]
                elif (data.ndim == 2):
                    #  move the existing data - need to move from right to left
                    #  to avoid overwriting data yet to be moved
                    data[move_index[::-1], :] = data[move_idx[::-1],:]
                    #  and insert the new data
                    data[insert_index, :] = data_to_insert[:,:]
                else:
                    #  at some point do we handle 3d arrays?
                    pass

        #  now update our global properties
        if (obj_to_insert.channel_id not in self.channel_id):
            self.channel_id += obj_to_insert.channel_id

        #  update the n_pings attribute
        self.n_pings = self.ping_time.shape[0]


    def trim(self, n_pings=None, n_samples=None):
        """
        trim deletes pings from an echolab2 data object to a given length
        """

        if (not n_pings):
            n_pings = self.n_pings
        if (not n_samples):
            n_samples = self.n_samples

        #  resize keeping the sample number the same
        self.resize(n_pings, n_samples)


    def roll(self, roll_pings):
        """
        roll rolls our data array elements along the ping axis.

        Elements that roll beyond the last position are re-introduced at the first.
        """

        #TODO: Test these inline rolling functions
        #      Need to profile this code to see which methods are faster. Currently all rolling is
        #      implemented using np.roll which makes a copy of the data.
        #TODO: verify rolling direction
        #      Verify the correct rolling direction for both the np.roll calls and the 2 inline
        #      functions. I *think* the calls to np.roll are correct and the inline functions roll
        #      the wrong way.

        def roll_1d(data, n):
            #  rolls a 1d mostly in place
            #  based on code found here:
            #    https://stackoverflow.com/questions/35916201/alternative-to-numpy-roll-without-copying-array
            #  THESE HAVE NOT BEEN TESTED
            temp_view = data[:-n]
            temp_copy = data[-n]
            data[n:] = temp_view
            data[0] = temp_copy

        def roll_2d(data, n):
            #  rolls a 2d mostly in place
            temp_view = data[:-n,:]
            temp_copy = data[-n,:]
            data[n:,:] = temp_view
            data[0,:] = temp_copy

        #  work thru our list of attributes
        for attr_name in self._data_attributes:

            #  get a reference to this attribute
            attr = getattr(self, attr_name)

            #  resize the arrays using technique dependent on the array dimension
            if (attr.ndim == 1):
                attr = np.roll(attr, roll_pings)
                #attr[:] = roll_1d(attr, roll_pings)
            elif (attr.ndim == 2):
                attr = np.roll(attr, roll_pings, axis=0)
                #attr[:] = roll_2d(attr, roll_pings)

            #  update the attribute
            setattr(self, attr_name, attr)


    def resize(self, new_ping_dim, new_sample_dim):
        """
        resize_arrays iterates thru the provided list of attributes and
        resizes them in the instance of the object provided given the new
        array dimensions.
        """

        def _resize2d(data, ping_dim, sample_dim):
            """
            _resize2d returns a new array of the specified dimensions with the
            data from the provided array copied into it. This funciton is
            used when we need to resize 2d arrays along the minor axis as
            ndarray.resize and numpy.resize don't maintain the order of the
            data in these cases.
            """

            #  if the minor axis is changing we have to either concatenate or
            #  copy into a new resized array. I'm taking the second approach
            #  for now as I don't think there are performance differences
            #  between the two approaches.

            #  create a new array
            new_array = np.empty((ping_dim, sample_dim))
            #  fill it with NaNs
            new_array.fill(np.nan)
            #  copy the data into our new array
            new_array[0:data.shape[0], 0:data.shape[1]] = data
            #  and return it
            return new_array

        #  store the old sizes
        old_sample_dim = self.n_samples
        old_ping_dim = self.ping_time.shape[0]

        #  ensure our values are ints - some platforms/versions don't automagically
        #  coerce floats to ints when used as integer args
        new_ping_dim = int(new_ping_dim)
        new_sample_dim = int(new_sample_dim)

        #  work thru our list of attributes
        for attr_name in self._data_attributes:

            #  get a reference to this attribute
            attr = getattr(self, attr_name)

            #  resize the arrays using technique dependent on the array dimension
            if (attr.ndim == 1):
                #  1d arrays can be on the ping axes or sample axes and have to be handeld differently
                if (attr.shape[0] == old_sample_dim != new_sample_dim):
                    #  resize this sample axes attribute
                    attr = np.resize(attr,(new_sample_dim))
                elif (attr.shape[0] == old_ping_dim != new_ping_dim):
                    #  resize this ping axes attribute
                    attr = np.resize(attr,(new_ping_dim))
            elif (attr.ndim == 2):
                #  resize this 2d sample data array
                if (new_sample_dim == old_sample_dim):
                    #  if the minor axes isn't changing we can use ndarray.resize()
                    attr = np.resize(attr,(new_ping_dim, new_sample_dim))
                else:
                    #  if the minor axes is changing we need to use our resize2d function
                    attr = _resize2d(attr, new_ping_dim, new_sample_dim)

            #  update the attribute
            setattr(self, attr_name, attr)

        #  set the new sample count
        self.n_samples = new_sample_dim

        #  we cannot update the n_pings attribute here since raw_data uses this attribute
        #  to store the number of pings read, *not* the total number of pings in the array.
        #  as the processed_data class uses it. Instead we have to set it either in the
        #  child class or when context permits in other methods of this class.


    def get_indices(self, start_ping=None, end_ping=None, start_time=None,
                    end_time=None, time_order=True):
        """
        get_indices returns a boolean index array containing where the indices in the range
        defined by the times and/or ping numbers provided are True. By default the indexes
        are in time order. If time_order is set to False, the data will be returned in the
        order they occur in the data arrays.

        Note that pings with "empty" times (ping time == NaT) will be sorted to the
        beginning of the index array.
        """

        #  generate the ping number vector - we start counting pings at 1
        ping_number = np.arange(self.n_pings) + 1

        #  if starts and/or ends are omitted, assume fist and last respectively
        if (start_ping == start_time == None):
            start_ping = ping_number[0]
        if (end_ping == end_time == None):
            end_ping = ping_number[-1]

        #  get the primary index
        if (time_order):
            #  return indices in time order - note that empty ping times will be
            #  sorted to the front
            primary_index = self.ping_time.argsort()
        else:
            #  return indices in ping order
            primary_index = ping_number - 1

        #  generate a boolean mask of the values to return
        if (start_time):
            mask = self.ping_time[primary_index] >= start_time
        elif (start_ping >= 1):
            mask = ping_number[primary_index] >= start_ping
        if (end_time):
            mask = np.logical_and(mask, self.ping_time[primary_index] <= end_time)
        elif (end_ping >= 2):
            mask = np.logical_and(mask, ping_number[primary_index] <= end_ping)

        #  and return the indices that are included in the specified range
        return primary_index[mask]


    def _vertical_resample(self, data, sample_intervals, unique_sample_intervals,
            resample_interval, sample_offsets, min_sample_offset, is_power=True):
        """
        vertical_resample er, vertically resamples sample data given a target sample interval.
        This function also shifts samples vertically based on their sample offset so they
        are positioned correctly relative to each other. The first sample in the resulting
        array will have an offset that is the minimum of all offsets in the data.
        """

        #  determine the number of pings in the new array
        n_pings = data.shape[0]

        # check if we need to substitute our resample_interval value
        if (resample_interval == 0):
            #  resample to the shortest sample interval in our data
            resample_interval = min(unique_sample_intervals)
        elif (resample_interval == 1):
            #  resample to the longest sample interval in our data
            resample_interval = max(unique_sample_intervals)

        #  generate a vector of sample counts - generalized method that works with both
        #  raw_data and processed_data classes that finds the first non-NaN value searching
        #  from the "bottom up"
        sample_counts = data.shape[1] - np.argmax(~np.isnan(np.fliplr(data)), axis=1)

        #  create a couple of dictionaries to store resampling parameters by sample interval
        #  they will be used again when we fill the output array with the resampled data.
        resample_factor = {}
        rows_this_interval = {}
        sample_offsets_this_interval = {}

        #  determine number of samples in the output array - to do this we must loop thru
        #  the sample intervals, determine the resampling factor, then find the maximum sample
        #  count at that sample interval (taking into account the sample's offset) and multiply
        #  by the resampling factor to determine the max number of samples for that sample interval.
        new_sample_dims = 0
        for sample_interval in unique_sample_intervals:
            #  determine the resampling factor
            if (resample_interval > sample_interval):
                #  we're reducing resolution - determine the number of samples to average
                resample_factor[sample_interval] = resample_interval / sample_interval
            else:
                #  we're increasing resolution - determine the number of samples to expand
                resample_factor[sample_interval] = sample_interval / resample_interval

            #  determine the rows in this subset with this sample interval
            rows_this_interval[sample_interval] = np.where(sample_intervals == sample_interval)[0]

            #  determine the net vertical shift for the samples with this sample interval
            sample_offsets_this_interval[sample_interval] = sample_offsets[rows_this_interval[sample_interval]] - \
                    min_sample_offset

            #  and determine the maximum number of samples for this sample interval - this has to
            #  be done on a row-by-row basis since sample number can change on the fly. We include
            #  the sample offset to ensure we have room to shift our samples vertically by the offset
            max_samples_this_sample_int = max(sample_counts[rows_this_interval[sample_interval]] +
                    sample_offsets_this_interval[sample_interval])
            max_dim_this_sample_int = int(round(max_samples_this_sample_int * resample_factor[sample_interval]))
            if (max_dim_this_sample_int > new_sample_dims):
                    new_sample_dims = max_dim_this_sample_int

        #  now that we know the dimensions of the output array create the it and fill with NaNs
        resampled_data = np.empty((n_pings, new_sample_dims), dtype=self.sample_dtype, order='C')
        resampled_data.fill(np.nan)

        #  and fill it with data - We loop thru the sample intervals and within an interval extract slices
        #  of data that share the same number of samples (to reduce looping). We then determine if we're
        #  expanding or shrinking the number of samples. If expanding we simply replicate existing sample
        #  data to fill out the expaned array. If reducing, we take the mean of the samples. Power data is
        #  converted to linear units before the mean is computed and then transformed back.
        for sample_interval in unique_sample_intervals:
            #  determine the unique sample_counts for this sample interval
            unique_sample_counts = np.unique(sample_counts[rows_this_interval[sample_interval]])
            for count in unique_sample_counts:
                #  determine if we're reducing, expanding, or keeping the same number of samples
                if (resample_interval > sample_interval):
                    #  we're reducing the number of samples

                    #  if we're resampling power convert power to linear units
                    if (is_power):
                        this_data = np.power(data[rows_this_interval[sample_interval]]
                                [sample_counts[rows_this_interval[sample_interval]] == count] / 20.0, 10.0)

                    #  reduce the number of samples by taking the mean
                    this_data =  np.mean(this_data.reshape(-1, int(resample_factor[sample_interval])), axis=1)

                    if (is_power):
                        #  convert power back to log units
                        this_data = 20.0 * np.log10(this_data)

                elif (resample_interval < sample_interval):
                    #  we're increasing the number of samples

                    #  replicate the values to fill out the higher resolution array
                    this_data = np.repeat(data[rows_this_interval[sample_interval]]
                            [sample_counts[rows_this_interval[sample_interval]] == count][:,0:count],
                            int(resample_factor[sample_interval]), axis=1)

                else:
                    #  no change in resolution for this sample interval
                    this_data = data[rows_this_interval[sample_interval]] \
                            [sample_counts[rows_this_interval[sample_interval]] == count]

                #  generate the index array for this sample interval/sample count chunk of data
                rows_this_interval_count = rows_this_interval[sample_interval] \
                        [sample_counts[rows_this_interval[sample_interval]] == count]

                #  assign new values to output array - at the same time we will shift the data by sample offset
                unique_sample_offsets = np.unique(sample_offsets_this_interval[sample_interval])
                for offset in unique_sample_offsets:
                    resampled_data[rows_this_interval_count,
                            offset:offset + this_data.shape[1]]  = this_data

        #  return the resampled data and the sampling interval used
        return (resampled_data, resample_interval)


    def _vertical_shift(self, data, sample_offsets, unique_sample_offsets,
            min_sample_offset):
        """
        vertical_shift adjusts the output array size and pads the top of the
        samples array to vertically shift the positions of the sample data in the output
        array. Pings with offsets greater than the minimum will be padded on the top,
        shifting them into their correct location relative to the other pings.

        The result is an output array with samples that are properly aligned vertically
        relative to each other with a sample offset that is constant and equal to the
        minimum of the original sample offsets.

        This method is only called if our data has a constant sample interval but
        varying sample offsets. If the data has multiple sample intervals the offset
        adjustment is done in vertical_resample.
        """

        #  determine the new array size
        new_sample_dims = data.shape[1] + max(sample_offsets) - min_sample_offset

        #  create the new array
        shifted_data = np.empty((data.shape[0], new_sample_dims), dtype=self.sample_dtype, order='C')
        shifted_data.fill(np.nan)

        #  and fill it looping over the different sample offsets
        for offset in unique_sample_offsets:
            rows_this_offset = np.where(sample_offsets == offset)[0]
            start_index = offset - min_sample_offset
            end_index = start_index + data.shape[1]
            shifted_data[rows_this_offset, start_index:end_index] = data[rows_this_offset, 0:data.shape[1]]

        return shifted_data


    def _copy(self, obj):
        """
        _copy is an internal helper method that is called by child "copy"
        methods to copy the ping_data attributes as well as the
        data_attributes.
        """

        #  copy the common attributes
        obj.sample_dtype = self.sample_dtype
        obj.n_samples = self.n_samples
        obj.n_pings = self.n_pings
        obj._data_attributes = list(self._data_attributes)

        #  work through the data attributes list copying the values
        for attr_name in obj._data_attributes:
            attr = getattr(self, attr_name)
            setattr(obj, attr_name, attr.copy())

        #  return the copy
        return obj


    def _like(self, obj, n_pings, value, empty_times=False):
        """
        _like is an internal helper method that is called by "empty_like" and
        "zeros_like" methods of child classes which copy the ping_data attributes
        into the provided ping_data based object as well as creating "data" arrays
        that are filled with the specified value. All vertical axis will be copied
        without modification.

        If empty_times is False, the ping_time vector of this instance is copied
        to the new object. If it is True, the new ping_time vector is filled with
        NaT (not a time) values. IF n_pings != self.n_pings THIS ARGUMENT IS IGNORED
        AND THE NEW PING VECTOR IS FILLED WITH NaT.

        You can specify channel_id if you want to explicitly set it and not copy
        it from this instance.

        The result should be a new object where horizontal axes (excepting ping_time)
        and sample data arrays are empty (NaN or NaT). The contents of the ping_time
        vector will depend on the state of the empty_times keyword. The new object's
        shape will be (n_pings, self.n_samples)
        """
        #  if n_pings is None, we create an empty array with the same number of pings
        if (n_pings == None):
            n_pings = self.n_pings

        #  copy the common attributes
        obj.sample_dtype = self.sample_dtype
        obj.n_samples = self.n_samples
        obj.n_pings = n_pings

        obj._data_attributes = list(self._data_attributes)

        #  check if n_pings != self.n_pings - If the new object's horizontal axis is
        #  a different shape than this object's we can't copy ping_time data since
        #  there isn't a direct mapping and we don't know what the user wants here.
        #  This can/should be handled in the child method if needed.
        if (n_pings != self.n_pings):
            #  we have to force an empty ping_time vector since the axes differ
            empty_times = True

        #  create the dynamic attributes
        for attr_name in self._data_attributes:

            #  get the attribute
            attr = getattr(self, attr_name)

            if (attr.shape[0] == self.n_samples):
                #  copy all vertical axes w/o changing them
                data = attr.copy()
            else:
                #  create an array the appropriate shape filled with the specified value
                if (attr.ndim == 1):
                    #  create an array the same shape filled with the specified value
                    data = np.empty((n_pings), dtype=attr.dtype)

                    #  check if this is the ping_time attribute and if we should copy
                    #  this instances ping_time data or create an empty ping_time vector
                    if (attr_name == 'ping_time'):
                        if (empty_times):
                            data[:] = np.datetime64('NaT')
                        else:
                            data[:] = attr.copy()
                    #  other time based attribuets are set to NaT - not sure if this is
                    #  what we want to do, but not sure what other time attributes would
                    #  exist so this is what we're doing for now
                    elif data.dtype == 'datetime64[ms]':
                        data[:] = np.datetime64('NaT')
                    else:
                        data[:] = value
                else:
                    #  create the 2d array(s)
                    data = np.empty((n_pings, self.n_samples), dtype=attr.dtype)
                    data[:, :] = value

            #  add the attribute to our empty object - we can skip using add_attribute
            #  here because we shouldn't need to check dimensions and we've already handled
            #  the low level stuff like copying the _data_sttributes list, etc.
            setattr(obj, attr_name, data)

        return obj