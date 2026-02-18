def handle(self, message):

    regex_result = self.regex.parse(message)

    if regex_result:
        return regex_result

    return self.llm.extract(message)
