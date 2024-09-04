package com.vasworks.android.util;

/**
 * Key and Value
 */
public class KeyValue {
    public String key;
    public String value;

    /**
     * @param key
     * @param value
     */
    public KeyValue(final String key, final String value) {
        super();
        this.key = key;
        this.value = value;
    }

	@Override
	public String toString() {
		return value;
	}

}