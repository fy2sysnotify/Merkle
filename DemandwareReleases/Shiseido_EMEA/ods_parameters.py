import constants as const

ods_config = {
    "realm": "bjxb",
    "ttl": 360,
    "settings": {
        "ocapi": [
            {
                "client_id": const.client_id,
                "resources": [
                    {
                        "resource_id": "/**",
                        "methods": [
                            "get",
                            "post",
                            "put",
                            "patch",
                            "delete"
                        ],
                        "read_attributes": "(**)",
                        "write_attributes": ""
                    }
                ]
            }
        ],
        "webdav": [
            {
                "client_id": const.client_id,
                "permissions": [
                    {
                        "path": "/cartridges",
                        "operations": [
                            "read_write"
                        ]
                    },
                    {
                        "path": "/impex",
                        "operations": [
                            "read_write"
                        ]
                    }
                ]
            }
        ]
    }
}