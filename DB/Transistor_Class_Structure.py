class Transistor:
    """Groups data of all other classes for a single transistor. Methods are specified in such a way that only
    user-interaction with this class is necessary (ToDo!)
    Documentation on how to add or extract a transistor-object to/from the database can be found in (ToDo!)
    """
    # name: str  # Name of the transistor. Choose as specific as possible.
    # transistor_type: str  # MOSFET or IGBT
    # These are documented in their respective class definitions
    # switch: Switch = Switch()
    # diode: Diode = Diode()
    # meta: Metadata = Metadata()
    # # Thermal data. See git for equivalent thermal circuit diagram.
    # r_th_cs: float  # Unit: K/W
    # r_th_switch: float  # Unit: K/W
    # r_th_diode_cs: float  # Unit: K/W
    # # Absolute maximum ratings
    # v_max: float  # Unit: V
    # i_max: float  # Unit: A

    def __init__(self, name, transistor_type, r_th_cs, r_th_switch,r_th_diode_cs, v_max,i_max, author, meta_type,template_version, template_date, creation_date, last_modified, comment, manufacturer,datasheet_hyperlink, datasheet_date, datasheet_version, housing_area, contact_area,r_th_total, r_th_vector, c_th_total, c_th_vector, tau_total, tau_vector, transient_data):
        self.name = name                        # Name of the transistor. Choose as specific as possible.
        self.type = transistor_type             # MOSFET or IGBT
        self.r_th_cs = r_th_cs                  # Unit: K/W
        self.r_th_switch = r_th_switch          # Unit: K/W
        self.r_th_diode_cs = r_th_diode_cs      # Unit: K/W
        # Absolute maximum ratings
        self.v_max = v_max                      # Unit: V
        self.i_max = i_max                      # Unit: A
        self.Metadata = self.Metadata(author, meta_type,template_version, template_date, creation_date, last_modified, comment, manufacturer,datasheet_hyperlink, datasheet_date, datasheet_version, housing_area, contact_area)
        self.FosterThermalModel = self.FosterThermalModel(r_th_total, r_th_vector, c_th_total, c_th_vector, tau_total, tau_vector, transient_data)

    class Metadata:
        """Contains metadata of the transistor/switch/diode. Only used to not bloat the other classes. The attributes
        ending on _date are set automatically each time a relevant change to other attributes is made (ToDo!)"""
        # # User-specific data
        # author: str
        # comment: str
        # # Date and template data. Should not be changed manually.
        # template_version: str
        # template_date: datetime.date
        # creation_date: datetime.date = datetime.date.today()
        # last_modified: datetime.date = datetime.date.today()
        # # Manufacturer- and part-specific data
        # manufacturer: str
        # meta_type: str  # Specific manufacturer dependent type
        # datasheet_hyperlink: str  # Make sure this link is valid.
        # datasheet_date: datetime.date  # Should not be changed manually.
        # datasheet_version: str
        # housing_are: float  # Unit: mm^2
        # cooling_area: float  # Unit: mm^2

        def __init__(self, author, meta_type,template_version, template_date, creation_date, last_modified, comment, manufacturer,datasheet_hyperlink, datasheet_date, datasheet_version, housing_area, contact_area):
            self.author = author
            self.meta_type = meta_type
            self.template_version = template_version
            self.template_date = template_date
            self.creation_date = creation_date
            self.last_modified = last_modified
            self.comment = comment
            self.manufacturer = manufacturer
            self.datasheet_hyperlink = datasheet_hyperlink
            self.datasheet_date = datasheet_date
            self.datasheet_version = datasheet_version
            self.housing_area = housing_area
            self.contact_area = contact_area

    class FosterThermalModel:
        """Contains data to specify parameters of the Foster thermal model. This model describes the transient temperature
        behavior as a thermal RC-network. The necessary parameters can be estimated by curve-fitting transient temperature
        data supplied in transient_data (ToDo!)
        or by manually specifying the individual 2 out of 3 of the parameters R, C, and tau.(ToDo!)"""
        # # Thermal resistances of RC-network (array).
        # r_th_vector: "np.ndarray[np.float64]"  # Unit: K/W
        # # Sum of thermal resistances of n-pole RC-network (scalar).
        # r_th_total: float  # Unit: K/W
        # # Thermal capacitances of n-pole RC-network (array).
        # c_th_vector: "np.ndarray[np.float64]"  # Unit: J/K
        # # Sum of thermal capacitances of n-pole low pass as (scalar).
        # c_th_total: float  # Unit: J/K
        # # Thermal time constants of n-pole RC-network (array).
        # tau_total: float  # Unit: s
        # # Sum of thermal time constants of n-pole RC-network (scalar).
        # tau_vector: "np.ndarray[np.float64]"
        # # Transient data for extraction of the thermal parameters specified above.
        # # Represented as a 2xm Matrix where row 1 is the time and row 2 the temperature.
        # transient_data: "np.ndarray[np.float64]"

        def __init__(self, r_th_total, r_th_vector, c_th_total, c_th_vector, tau_total, tau_vector, transient_data):
            self.r_th_total = r_th_total
            self.r_th_vector = r_th_vector
            self.c_th_total = c_th_total
            self.c_th_vector = c_th_vector
            self.tau_total = tau_total
            self.tau_vector = tau_vector
            self.transient_data = transient_data

    class TestInner:

        def __init__(self, surname):
            self.surname = surname

    class TestInner:

        def __init__(self, surname):
            self.surname = surname