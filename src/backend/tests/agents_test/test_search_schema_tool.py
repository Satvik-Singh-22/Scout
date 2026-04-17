# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import unittest
import types
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from backend.agents.tools.search_schema_tool import search_schema


class TestSearchSchemaTool(unittest.TestCase):
    @patch("backend.agents.tools.search_schema_tool._get_embed_model")
    @patch("backend.agents.tools.search_schema_tool.os.getenv")
    def test_returns_empty_string_when_pinecone_query_fails(
        self,
        mock_getenv,
        mock_get_embed_model,
    ):
        def getenv_side_effect(key, default=""):
            if key == "PINECONE_API_KEY":
                return "test-key"
            if key == "PINECONE_INDEX_NAME":
                return "test-index"
            return default

        mock_getenv.side_effect = getenv_side_effect

        mock_embed_model = MagicMock()
        mock_embed_model.encode.return_value.tolist.return_value = [0.1, 0.2]
        mock_get_embed_model.return_value = mock_embed_model

        mock_index = MagicMock()
        mock_index.query.side_effect = RuntimeError("HTTP 500")

        mock_pinecone_cls = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index
        fake_module = types.ModuleType("pinecone")
        fake_module.Pinecone = mock_pinecone_cls

        with patch.dict(sys.modules, {"pinecone": fake_module}):
            result = search_schema.invoke({"search_keyword": "transaction volume"})
        self.assertEqual(result, {"schema_string": "", "table_names": []})


if __name__ == "__main__":
    unittest.main()
