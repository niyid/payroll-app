package com.vasworks.xmlrpc.serializer;

import org.w3c.dom.Element;

import com.vasworks.xmlrpc.XMLRPCException;
import com.vasworks.xmlrpc.xmlcreator.XmlElement;

/**
 *
 * @author Tim Roes
 */
public class NullSerializer implements Serializer {

	public Object deserialize(Element content) throws XMLRPCException {
		return null;
	}

	public XmlElement serialize(Object object) {
		return new XmlElement(SerializerHandler.TYPE_NULL);
	}

}