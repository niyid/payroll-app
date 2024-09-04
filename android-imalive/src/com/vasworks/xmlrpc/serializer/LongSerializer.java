package com.vasworks.xmlrpc.serializer;

import org.w3c.dom.Element;

import com.vasworks.xmlrpc.XMLRPCException;
import com.vasworks.xmlrpc.XMLUtil;
import com.vasworks.xmlrpc.xmlcreator.XmlElement;

/**
 *
 * @author Tim Roes
 */
class LongSerializer implements Serializer {

	public Object deserialize(Element content) throws XMLRPCException {
		return Long.parseLong(XMLUtil.getOnlyTextContent(content.getChildNodes()));
	}

	public XmlElement serialize(Object object) {
		return XMLUtil.makeXmlTag(SerializerHandler.TYPE_LONG,
				((Long)object).toString());
	}

}
