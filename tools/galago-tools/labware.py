from pydantic import BaseModel

class Labware(BaseModel):
    name: str
    #part_number: str
    #manuacturer: str
    width : float
    height: float 
    zoffset: float
    plate_lid_offset: float #offset when the lid is on the plate
    lid_offset: float #offset when lid is on nest



class LabwareDb():

    def __init__(self) -> None:
        self.all_labware : list[Labware]

        self.all_labware = [
            Labware(name='default', zoffset=0, width=125, height=14,plate_lid_offset=0,lid_offset=0),
            Labware(name='6-well celltreat', width=125,zoffset=2, height=20,plate_lid_offset=-2,lid_offset=2),
            Labware(name='24-well celltreat', width=125, zoffset=0, height=15,plate_lid_offset=0,lid_offset=0),
            Labware(name='48-well celltreat', width=125, zoffset=0, height=15,plate_lid_offset=0,lid_offset=0),
            Labware(name='384-well celltreat', width=125, zoffset=1.0, height=15,plate_lid_offset=-2.5,lid_offset=4),
            Labware(name='96-well Phenoplate', width=125, zoffset=0, height=15,plate_lid_offset=-2,lid_offset=0),
            Labware(name='96-well deepwell',  width=125, zoffset=12, height=44,plate_lid_offset=-2.5,lid_offset=4),
            Labware(name='96-well Twist Plate', width=125, zoffset=4.5, height=15,plate_lid_offset=0,lid_offset=0),
            Labware(name='96-Well Twist Plate', width=125, zoffset=4.5, height=15,plate_lid_offset=0,lid_offset=0)
        ]
    
    def get_all_labware(self) -> list[Labware]:
        return self.all_labware

    def get_labware(self, labware_name:str) -> Labware:
        if len(self.all_labware) == 0:
            raise RuntimeError('Labware database is empty.')
        return next(lw for lw in self.all_labware if lw.name == labware_name)
