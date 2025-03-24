import constants as const

create_json = {
    "realm": "bjxb",
    "ttl": 0,
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