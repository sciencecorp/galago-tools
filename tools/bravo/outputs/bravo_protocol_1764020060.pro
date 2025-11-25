<?xml version='1.0' encoding='ASCII' ?>
<Velocity11 file='Protocol_Data' md5sum='' version='2.0' >
	<File_Info AllowSimultaneousRun='1' AutoExportGanttChart='0' AutoLoadRacks='When the main protocol starts' AutoUnloadRacks='0' AutomaticallyLoadFormFile='1' Barcodes_Directory='' ClearInventory='0' DeleteHitpickFiles='1' Description='' Device_File='/Users/silvioo/Documents/git_projects/galago-tools/tools/bravo/multiple_devices.dev' Display_User_Task_Descriptions='1' DynamicAssignPlateStorageLoad='0' FinishScript='' Form_File='' HandlePlatesInInstance='1' ImportInventory='0' InventoryFile='' Notes='' PipettePlatesInInstanceOrder='0' Protocol_Alias='' StartScript='' Use_Global_JS_Context='0' />
	<Processes >
		<Main_Processes >
			<Process >
				<Minimized >0</Minimized>
				<Task Name='Bravo::SubProcess' >
					<Enable_Backup >0</Enable_Backup>
					<Task_Disabled >0</Task_Disabled>
					<Task_Skipped >0</Task_Skipped>
					<Has_Breakpoint >0</Has_Breakpoint>
					<Advanced_Settings />
					<TaskScript Name='TaskScript' Value='' />
					<Parameters >
						<Parameter Category='' Name='Sub-process name' Value='Bravo SubProcess 1' />
						<Parameter Category='Static labware configuration' Name='Display confirmation' Value="Don't display" />
						<Parameter Category='Static labware configuration' Name='1' Value='96 V11 LT250 Tip Box Standard' />
						<Parameter Category='Static labware configuration' Name='2' Value='96 V11 LT250 Tip Box Standard' />
						<Parameter Category='Static labware configuration' Name='3' Value='96 V11 LT250 Tip Box Standard' />
						<Parameter Category='Static labware configuration' Name='4' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
						<Parameter Category='Static labware configuration' Name='5' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
						<Parameter Category='Static labware configuration' Name='6' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
						<Parameter Category='Static labware configuration' Name='7' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
						<Parameter Category='Static labware configuration' Name='8' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
						<Parameter Category='Static labware configuration' Name='9' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					</Parameters>
					<Parameters >
						<Parameter Centrifuge='0' Name='SubProcess_Name' Pipettor='1' Value='Bravo SubProcess 1' />
					</Parameters>
				</Task>
				<Plate_Parameters >
					<Parameter Name='Plate name' Value='process - 1' />
					<Parameter Name='Plate type' Value='' />
					<Parameter Name='Simultaneous plates' Value='1' />
					<Parameter Name='Plates have lids' Value='0' />
					<Parameter Name='Plates enter the system sealed' Value='0' />
					<Parameter Name='Use single instance of plate' Value='0' />
					<Parameter Name='Automatically update labware' Value='0' />
					<Parameter Name='Enable timed release' Value='0' />
					<Parameter Name='Release time' Value='30' />
					<Parameter Name='Auto managed counterweight' Value='0' />
					<Parameter Name='Barcode filename' Value='No Selection' />
					<Parameter Name='Has header' Value='' />
					<Parameter Name='Barcode or header South' Value='No Selection' />
					<Parameter Name='Barcode or header West' Value='No Selection' />
					<Parameter Name='Barcode or header North' Value='No Selection' />
					<Parameter Name='Barcode or header East' Value='No Selection' />
				</Plate_Parameters>
				<Quarantine_After_Process >0</Quarantine_After_Process>
			</Process>
			<Pipette_Process Name='Bravo SubProcess 1' >
				<Minimized >0</Minimized>
				<Task Name='Bravo::secondary::Initialize axis' Task_Type='1024' >
					<Enable_Backup >0</Enable_Backup>
					<Task_Disabled >0</Task_Disabled>
					<Task_Skipped >0</Task_Skipped>
					<Has_Breakpoint >0</Has_Breakpoint>
					<Advanced_Settings >
						<Setting Name='Estimated time' Value='5.0' />
					</Advanced_Settings>
					<TaskScript Name='TaskScript' Value='' />
					<Parameters >
						<Parameter Category='' Name='Axis' Value='X' />
						<Parameter Category='' Name='Initialize even if already homed' Value='1' />
						<Parameter Category='Task Description' Name='Task description' Value='Initialize axis X (Bravo)' />
						<Parameter Category='Task Description' Name='Use default task description' Value='1' />
						<Parameter Category='Task Description' Name='Task number' Value='1' />
					</Parameters>
					<PipetteHead AssayMap='0' Disposable='1' HasTips='1' MaxRange='251' MinRange='-41' Name='96LT, 200 µL Series III' >
						<PipetteHeadMode Channels='0' ColumnCount='12' RowCount='8' SubsetConfig='0' SubsetType='0' TipType='1' />
					</PipetteHead>
				</Task>
				<Devices >
					<Device Device_Name='Agilent Bravo - 1' Location_Name='Default Location' />
				</Devices>
				<Parameters >
					<Parameter Name='Display confirmation' Value="Don't display" />
					<Parameter Name='1' Value='96 V11 LT250 Tip Box Standard' />
					<Parameter Name='2' Value='96 V11 LT250 Tip Box Standard' />
					<Parameter Name='3' Value='96 V11 LT250 Tip Box Standard' />
					<Parameter Name='4' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					<Parameter Name='5' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					<Parameter Name='6' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					<Parameter Name='7' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					<Parameter Name='8' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
					<Parameter Name='9' Value='96 Greiner 655101 PS Clr Rnd Well Flat Btm' />
				</Parameters>
				<Dependencies />
			</Pipette_Process>
		</Main_Processes>
	</Processes>
</Velocity11>