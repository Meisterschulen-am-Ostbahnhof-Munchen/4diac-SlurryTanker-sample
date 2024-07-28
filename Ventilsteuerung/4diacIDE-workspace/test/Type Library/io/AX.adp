<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="AX" Comment="Adapter Interface">
	<Identification Standard="61499-1">
	</Identification>
	<VersionInfo Version="1.0" Author="franz" Date="2024-04-24">
	</VersionInfo>
	<CompilerInfo>
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="E1" Type="Event" Comment="Indication (or Request)">
				<With Var="D1"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="D1" Type="BOOL" Comment="Indication (or Request) Data from Plug"/>
		</OutputVars>
	</InterfaceList>
	<Service RightInterface="SOCKET" LeftInterface="PLUG" Comment="Adapter Interface">
		<ServiceSequence Name="request_confirm" Comment="">
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="REQ" Parameters="REQD"/>
				<OutputPrimitive Interface="PLUG" Event="REQ" Parameters="REQD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="CNF" Parameters="CNFD"/>
				<OutputPrimitive Interface="SOCKET" Event="CNF" Parameters="CNFD"/>
			</ServiceTransaction>
		</ServiceSequence>
		<ServiceSequence Name="indication_response" Comment="">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="IND" Parameters="INDD"/>
				<OutputPrimitive Interface="SOCKET" Event="IND" Parameters="INDD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="RSP" Parameters="RSPD"/>
				<OutputPrimitive Interface="PLUG" Event="RSP" Parameters="RSPD"/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
</AdapterType>
