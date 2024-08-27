class DexClassBase:
    def test_fetch_pools_reserve_info(
        self, dex_instance, list_of_pool_info, expect_reserve_count
    ):
        result = dex_instance.fetch_pools_reserve_info(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        assert len(result) == len(list_of_pool_info)
        for pool_info, _expect_reserve_count in zip(
            list_of_pool_info, expect_reserve_count
        ):
            pool_address = pool_info.address
            assert pool_address in result
            assert isinstance(result[pool_address], (tuple, dict))
            assert len(result[pool_address]) == _expect_reserve_count, (
                f"pool_address: {pool_address}, "
                f"result: {len(result[pool_address])}, "
                f"expect: {_expect_reserve_count}"
            )

    def test_fetch_pools_token_addresses(
        self, dex_instance, list_of_pool_info, expect_token_address_count
    ):
        result = dex_instance.fetch_pools_token_addresses(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        assert len(result) == len(list_of_pool_info)

        for pool_info, _expect_token_address_count in zip(
            list_of_pool_info, expect_token_address_count
        ):
            pool_address = pool_info.address
            expect_token_addresses = [
                token.lower() for token in pool_info.token_addresses
            ]
            assert pool_address in result
            assert isinstance(result[pool_address], tuple)
            assert len(result[pool_address]) == _expect_token_address_count
            for idx in range(len(result[pool_address])):
                assert result[pool_address][idx] in expect_token_addresses

    def test_fetch_pools_fee(self, dex_instance, list_of_pool_info, expect_fee):
        result = dex_instance.fetch_pools_fee(
            [pool_info.address for pool_info in list_of_pool_info]
        )
        assert len(result) == len(list_of_pool_info)
        for pool_info, _expect_fee in zip(list_of_pool_info, expect_fee):
            pool_address = pool_info.address
            assert pool_address in result
            assert isinstance(result[pool_address], int)
            assert result[pool_address] == _expect_fee

    def test_calculate_price(self, dex_instance, list_of_pool_info, token_decimals):
        for pool_info, _token_decimals in zip(list_of_pool_info, token_decimals):
            result = dex_instance.calculate_price(
                pool_info,
                pool_info.token_addresses[0],
                pool_info.token_addresses[1],
                _token_decimals[0],
                _token_decimals[1],
            )
            assert isinstance(result, float)
            assert result > 0
