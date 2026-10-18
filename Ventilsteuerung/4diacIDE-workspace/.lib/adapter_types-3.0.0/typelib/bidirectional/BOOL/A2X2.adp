<?xml version="1.0" encoding="UTF-8"?>
<AdapterType Name="A2X2" Comment="bidirectional Adapter Interface for 2 Events and 2 Bools">
	<Identification Standard="61499-1" Description="Copyright (c) 2026 HR Agrartechnik GmbH  &#10; &#10;This program and the accompanying materials are made  &#10;available under the terms of the Eclipse Public License 2.0  &#10;which is available at https://www.eclipse.org/legal/epl-2.0/  &#10; &#10;SPDX-License-Identifier: EPL-2.0">
	</Identification>
	<VersionInfo Organization="HR Agrartechnik GmbH" Version="1.0" Author="Franz Höpfinger" Date="2026-08-31" Remarks="Initial Version">
	</VersionInfo>
	<CompilerInfo packageName="adapter::types::bidirectional">
	</CompilerInfo>
	<InterfaceList>
		<EventInputs>
			<Event Name="EI_UP" Type="Event" Comment="UP Request (or Indication)">
				<With Var="DI_UP"/>
			</Event>
			<Event Name="EI_DOWN" Type="Event" Comment="DOWN Request (or Indication)">
				<With Var="DI_DOWN"/>
			</Event>
		</EventInputs>
		<EventOutputs>
			<Event Name="EO_UP" Type="Event" Comment="UP Indication (or Request)">
				<With Var="DO_UP"/>
			</Event>
			<Event Name="EO_DOWN" Type="Event" Comment="DOWN Indication (or Request)">
				<With Var="DO_DOWN"/>
			</Event>
		</EventOutputs>
		<InputVars>
			<VarDeclaration Name="DI_UP" Type="BOOL" Comment="TRUE = forward, up, right, clockwise"/>
			<VarDeclaration Name="DI_DOWN" Type="BOOL" Comment="TRUE = backward, down, left, counter-clockwise"/>
		</InputVars>
		<OutputVars>
			<VarDeclaration Name="DO_UP" Type="BOOL" Comment="TRUE = forward, up, right, clockwise"/>
			<VarDeclaration Name="DO_DOWN" Type="BOOL" Comment="TRUE = backward, down, left, counter-clockwise"/>
		</OutputVars>
	</InterfaceList>
	<Attribute Name="eclipse4diac::core::TypeHash" Value="''"/>
</AdapterType>
