<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="A2X" Comment="unidirectional Adapter Interface for 2 Events and 2 Bools">
	<Identification Standard="61499-1" Description="Copyright (c) 2024 HR Agrartechnik GmbH &#10; &#10;This program and the accompanying materials are made &#10;available under the terms of the Eclipse Public License 2.0 &#10;which is available at https://www.eclipse.org/legal/epl-2.0/ &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2024-04-24" Remarks="Initial Version">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::unidirectional">
	</CompilerInfo>
	<InterfaceList>
		<EventOutputs>
			<Event Name="E_UP" Type="Event" Comment="UP">
				<With Var="UP"/>
			</Event>
			<Event Name="E_DOWN" Type="Event" Comment="DOWN">
				<With Var="DOWN"/>
			</Event>
		</EventOutputs>
		<OutputVars>
			<VarDeclaration Name="UP" Type="BOOL" Comment="TRUE = forward, up, right, clockwise"/>
			<VarDeclaration Name="DOWN" Type="BOOL" Comment="TRUE = backward, down, left, counter-clockwise"/>
		</OutputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
