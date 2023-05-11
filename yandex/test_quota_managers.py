class TestResourceQuotaManager:
    def test_have_resources(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 100,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 100,
                'user_memory': 100
            }
        }
        assert yt_quota_manager.available_slots() == yt_quota_manager.step

    def test_cpu_reached_limit(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 100,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 100 * (1 + yt_quota_manager.max_demand_usage_diff),
                'user_memory': 100
            }
        }
        assert yt_quota_manager.available_slots() == 0

    def test_ram_reached_limit(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 100,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 100,
                'user_memory': 100 * (1 + yt_quota_manager.max_demand_usage_diff)
            }
        }
        assert yt_quota_manager.available_slots() == 0

    def test_far_above_limit(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 100,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 100 * (1 + 2 * yt_quota_manager.max_demand_usage_diff),
                'user_memory': 100 * (1 + 2 * yt_quota_manager.max_demand_usage_diff)
            }
        }
        assert yt_quota_manager.available_slots() == 0

    def test_demand_less_than_usage(self, yt_quota_manager):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 100,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 50,
                'user_memory': 50
            }
        }
        assert yt_quota_manager.available_slots() == yt_quota_manager.step

    def test_yt_error(self, yt_quota_manager):
        yt_quota_manager.yt_client.get.side_effect = [Exception("YT ERROR")]
        assert yt_quota_manager.available_slots() == 0

    @pytest.mark.parametrize('various_max_demand_usage_diffs', [0.2], indirect=True)
    @pytest.mark.parametrize('various_steps', [4], indirect=True)
    def test_usage_in_the_middle(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 50,
                'user_memory': 100
            },
            'resource_demand': {
                'cpu': 50 + 0.5 * yt_quota_manager.max_demand_usage_diff * 50,
                'user_memory': 100 + 0.5 * yt_quota_manager.max_demand_usage_diff * 100
            }
        }
        assert 0 < yt_quota_manager.available_slots() < yt_quota_manager.step

    def test_invalid_yt_response(self, yt_quota_manager):
        yt_quota_manager.yt_client.get.return_value = {}
        assert yt_quota_manager.available_slots() == 0

    @pytest.mark.parametrize('various_max_demand_usage_diffs', [0.2], indirect=True)
    @pytest.mark.parametrize('various_steps', [1], indirect=True)
    def test_coef_close_to_one(self, yt_quota_manager, various_max_demand_usage_diffs, various_steps):
        yt_quota_manager.yt_client.get.return_value = {
            'resource_usage': {
                'cpu': 50,
                'user_memory': 50
            },
            'resource_demand': {
                'cpu': 51,
                'user_memory': 51
            }
        }
        assert yt_quota_manager.available_slots() == 1