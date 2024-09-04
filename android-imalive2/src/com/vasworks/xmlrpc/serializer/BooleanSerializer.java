package com.vasworks.xmlrpc.serializer;

import org.w3c.dom.Element;

import com.vasworks.xmlrpc.XMLRPCException;
import com.vasworks.xmlrpc.XMLUtil;
import com.vasworks.xmlrpc.xmlcreator.XmlElement;

/**
 *
 * @author Tim Roes
 */
public class BooleanSerializer implements Serializer {

	public Object deserialize(Element content) throws XMLRPCException {
		return XMLUtil.getOnlyTextContent(content.getChildNodes()).equals("1")
				? Boolean.TRUE : Boolean.FALSE;
	}

	public XmlElement serialize(Object object) {
		return XMLUtil.makeXmlTag(SerializerHandler.TYPE_BOOLEAN,
				(Boolean)object ? "1" : "0");
	}

}