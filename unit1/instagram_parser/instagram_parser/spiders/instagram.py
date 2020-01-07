# -*- coding: utf-8 -*-
import json
import re
import scrapy
from urllib.parse import urlencode
from copy import deepcopy
from scrapy.http import HtmlResponse
from instagram_parser.items import UserItem, FollowingItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    auth_url = 'https://www.instagram.com/accounts/login/ajax/'

    # todo: add authentications data
    user_data = {
        "username": "",
        "password": "",
    }
    users_list = {"haikson"}
    users_parsed = set()
    graphql_url = 'https://www.instagram.com/graphql/query/?{params}'
    graphql_hashes = {
        "user": "c9100bf9110dd6361671f113dd02e7d6",
        # {"user_id":"624689305","include_chaining":true,"include_reel":true,"include_suggested_users":true,"include_logged_out_extras":false,"include_highlight_reels":false,"include_related_profiles":false}
        "followers": "c76146de99bb02f6415203be841dd25a",
        # {"id":"624689305","include_reel":true,"fetch_mutual":false,"first":17,"after":"QVFBc3I0X0U5OW9OUHRjS1NRWHl5aml2ZDZHcGg4Yi0tSTdkb0p3WkE4ZWhsNWd3R2kwYXlJZ0NUZFJBQVhXQjE1Y0lCbHd3Ty1UY1BrVm1QLWhqZU5iMA=="}
        "following": "d04b0a864b4b54837c0d870b0e77e076"
        # {"id":"624689305","include_reel":true,"fetch_mutual":false,"first":24}
    }
    parse_limit = 200

    def parse(self, response):
        re_csrf = re.compile(r"\"csrf_token\":\"(\w+?)\"")
        csrf_token = re_csrf.findall(response.text)[0]
        form_data = deepcopy(self.user_data)
        headers = {
            "X-CSRFToken": csrf_token,
        }
        yield scrapy.FormRequest(
            self.auth_url,
            method='POST',
            callback=self.user_parse,
            formdata=form_data,
            headers=headers
        )


    def user_parse(self, response: HtmlResponse):
        auth_response = json.loads(response.text)
        if auth_response.get("authenticated"):
            for ig_user in self.users_list:
                yield response.follow(f"/{ig_user}/", callback=self.parse_user_data, cb_kwargs={'username': ig_user})

    def parse_user_data(self, response: HtmlResponse, username: str, user_id: int=None):
        user_id = user_id or self.get_user_id(response.text, username)
        user_data = self.get_user_data(response.text)
        full_name = user_data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user", {}).get("full_name", {})

        yield UserItem(user_id=user_id, username=username, full_name=full_name)
        if len(self.users_parsed) <= self.parse_limit:
            followers_url = self.get_graphql_url(
                query_hash_name="followers",
                variables=self.followers_variables(user_id=user_id)
            )
            yield response.follow(followers_url, callback=self.parse_followers, cb_kwargs={"username": username, "user_id": int(user_id)})

            following_url = self.get_graphql_url(
                query_hash_name="following",
                variables=self.followers_variables(user_id=user_id)
            )
            yield response.follow(following_url, callback=self.parse_following, cb_kwargs={"username": username, "user_id": int(user_id)})

    def parse_followers(self, response: HtmlResponse, username: str, user_id: int):
        self.users_parsed.add(username)
        data = json.loads(response.text)
        after = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("page_info", {}).get("end_cursor")
        has_next_page = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("page_info", {}).get("has_next_page")

        followers = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("edges", [])
        for follower in followers:
            follower = follower.get("node", {})
            if follower.get("username") not in self.users_parsed:
                if len(self.users_parsed) <= self.parse_limit:
                    yield response.follow(
                        "/{}/".format(follower.get("username")),
                        callback=self.parse_user_data,
                        cb_kwargs={"username": follower.get("username"), "user_id": follower.get("id")}
                    )
                yield FollowingItem(
                    user_id=int(follower.get('id')),
                    followers=[int(user_id)]
                )
        if has_next_page:
            followers_url = self.get_graphql_url(
                query_hash_name="followers",
                variables=self.followers_variables(user_id=user_id, after=after)
            )
            yield response.follow(
                followers_url,
                callback=self.parse_followers,
                cb_kwargs={"username": username, "user_id": user_id}
            )

    def parse_following(self, response: HtmlResponse, username: str, user_id: int):
        self.users_parsed.add(username)
        data = json.loads(response.text)
        after = data.get("data", {}).get("user", {}).get("edge_follow", {}).get("page_info", {}).get("end_cursor")
        has_next_page = data.get("data", {}).get("user", {}).get("edge_followed_by", {}).get("page_info", {}).get("has_next_page")

        followers = data.get("data", {}).get("user", {}).get("edge_follow", {}).get("edges", [])
        for follower in followers:
            follower = follower.get("node", {})
            if follower.get("username") not in self.users_parsed:
                yield response.follow(
                    "/{}/".format(follower.get("username")),
                    callback=self.parse_user_data,
                    cb_kwargs={"username": follower.get("username"), "user_id": follower.get("id")}
                )
                yield FollowingItem(
                    user_id=int(user_id),
                    followers=[int(follower.get('id'))]
                )
        if has_next_page:
            followers_url = self.get_graphql_url(
                query_hash_name="following",
                variables=self.followers_variables(user_id=user_id, after=after)
            )
            yield response.follow(
                followers_url,
                callback=self.parse_followers,
                cb_kwargs={"username": username, "user_id": user_id}
            )

    def get_user_id(self, text, username):
        matched = re.search("{\"id\":\"\\d+\",\"username\":\"%s\"}" % username, text).group()
        return json.loads(matched).get("id")

    def get_user_data(self, text):
        regex = r"window._sharedData.*?({.*}?);";
        matches = re.findall(regex, text)
        if len(matches):
            return json.loads(matches[0])
        return {}

    def get_graphql_url(self, query_hash_name, variables):
        if isinstance(variables, dict):
            variables = json.dumps(variables)
        return self.graphql_url.format(
            params=urlencode({"variables": variables, "query_hash":self.graphql_hashes[query_hash_name]})
        )

    @staticmethod
    def followers_variables(user_id, after=None):
        if isinstance(user_id, str):
            user_id = int(user_id)

        variables = {
            "id": "{}".format(user_id),
            "include_reel": True,
            "fetch_mutual": False,
            "first": 17,
        }
        if after:
            variables.update({"after": after})
        return variables