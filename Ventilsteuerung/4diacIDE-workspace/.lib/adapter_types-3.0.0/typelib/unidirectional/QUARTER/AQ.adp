<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="AQ" Comment="unidirectional Adapter Interface for 1 Event and 1 Byte (containing 2 bits)">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 Meisterschulen am Ostbahnhof&#10;&#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="Meisterschulen am Ostbahnhof" Version="1.0" Author="Franz Höpfinger" Date="2026-05-16" Remarks="Initial Version">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::unidirectional">
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="E1" Type="Event" Comment="Indication (or Request) Event from Plug">
				<With Var="D1"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="D1" Type="BYTE" Comment="Indication (or Request) Data from Plug (2 bits)"/>
		</OutputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
