<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="ATimeTick" Comment="Interface for a time out service roughly based on the definitions of ROOM">
	<Identification Standard="61499-1" Description="Copyright (c) 2017 fortiss GmbH&#10; &#10;This program and the accompanying materials are made&#10;available under the terms of the Eclipse Public License 2.0&#10;which is available at https://www.eclipse.org/legal/epl-2.0/&#10;&#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="3.1" Author="Franz Höpfinger" Date="2026-08-14" Remarks="FB_TON like cyclic Interface">
	</VersionInfo>
	<VersionInfo Version="3.0" Author="Patrick Aigner" Date="2025-04-14" Remarks="changed package">
	</VersionInfo>
	<VersionInfo Organization="fortiss GmbH" Version="1.0" Author="Alois Zoitl" Date="2017-09-22" Remarks="initial API and implementation and/or initial documentation">
	</VersionInfo>
	<CompilerInfo packageName="adapter::events::TimeOut">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="CNF" Type="Event" Comment="Execution Confirmation">
				<With Var="Q"/>
				<With Var="ET"/>
				<With Var="PT"/>
			</Event>
			<Event Name="STARTO_IN" Type="Event">
			</Event>
			<Event Name="STOPO_IN" Type="Event">
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="REQ" Type="Event" Comment="Normal Execution Request">
			</Event>
		</EventOutputs>
		<InputVars>
			<VarDeclaration Name="Q" Type="BOOL" Comment="is started = TRUE"/>
			<VarDeclaration Name="PT" Type="TIME" Comment="Process time"/>
			<VarDeclaration Name="ET" Type="TIME" Comment="Elapsed time"/>
		</InputVars>
	</InterfaceList>
	<Service RightInterface="PLUG" LeftInterface="SOCKET">
		<ServiceSequence Name="Timeout">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="START" Parameters="TD"/>
				<OutputPrimitive Interface="SOCKET" Event="START" Parameters="TD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="SOCKET" Event="TimeOut" Parameters=""/>
				<OutputPrimitive Interface="PLUG" Event="TimeOut"/>
			</ServiceTransaction>
		</ServiceSequence>
		<ServiceSequence Name="NormalOperation">
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="Start" Parameters="TD"/>
				<OutputPrimitive Interface="SOCKET" Event="Start" Parameters="TD"/>
			</ServiceTransaction>
			<ServiceTransaction>
				<InputPrimitive Interface="PLUG" Event="STOP" Parameters=""/>
				<OutputPrimitive Interface="SOCKET" Event="STOP" Parameters=""/>
			</ServiceTransaction>
		</ServiceSequence>
	</Service>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
