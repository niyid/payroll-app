package com.vasworks.xmlrpc;

/**
 *
 * @author Tim Roes
 */
public class XMLRPCRuntimeException extends RuntimeException {

	public XMLRPCRuntimeException(String ex) {
		super(ex);
	}

	public XMLRPCRuntimeException(Exception ex) {
		super(ex);
	}
	
}