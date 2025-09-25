import json
import shutil
from pathlib import Path

from .text import RichToken
from .text import Subsentence


def get_document_configuration(document):
    # This assumes that there is at least one sentence in a document, and that the tokenizer is uniform across all elements.
    # We may want to change this.
    # We also don't store any information about sentence tokenization, which we may also want to do
    sentences = document.sentences
    document_configuration = {
        "tokenizer": sentences[0].word_tokenizer.__class__.__name__,
        "taggers": [tagger.__class__.__name__ for tagger in sentences[0].taggers],
    }
    return document_configuration


class PlainTextCacher:
    def __init__(self, cache_location):
        self.cache_location = cache_location
        cache_path = Path(self.cache_location)
        if not cache_path.is_dir():
            cache_path.mkdir(parents=True, exist_ok=True)

    def cache_document(
        self,
        document,
        document_id,
        tags=None,
        save_subsentences=True,
        overwrite_cache=False,
    ):
        if tags is None:
            tags = ["ner_tag", "pos_tag"]

        # Save document configuration
        document_configuration = get_document_configuration(document)
        cache_location_root = str(Path(self.cache_location) / self._safe_document_id(document_id))
        cache_root_path = Path(cache_location_root)
        if not cache_root_path.is_dir():
            cache_root_path.mkdir(parents=True, exist_ok=True)
        elif overwrite_cache:
            shutil.rmtree(cache_location_root)
            cache_root_path.mkdir(parents=True, exist_ok=True)
        elif not overwrite_cache:
            raise AttributeError(
                "{document_id} is already cached! Enable overwrite_cache to overwrite the previous cache."
            )

        with open(self._document_config_path(cache_location_root), "w+") as f:
            json.dump(document_configuration, f)

        sentences = document.sentences

        # Save tokenisation
        with open(
            self._document_tokenizer_cache_path(
                cache_location_root, document_configuration["tokenizer"]
            ),
            "w+",
            encoding="utf-8",
        ) as f:
            for sentence in sentences:
                # We use silly emoji to delineate so that we don't ever get conflicts with actual tokens used.
                # It's 🙃 between words, and 🔥 between sentences
                f.write(str(("🙃".join(sentence.raw_tokens) + "🔥").encode("utf-8")))

        # Save start and end spans
        with open(
            self._document_tag_cache_path(cache_location_root, "start_end"),
            "w+",
            encoding="utf-8",
        ) as f:
            for sentence in sentences:
                indices = [[token.start, token.end] for token in sentence.tokens]
                f.write(str(indices) + "\n")

        # Save tags
        for tag in tags:
            # Should we be more careful so that we always get the same tagger for each tag?
            with open(
                self._document_tag_cache_path(cache_location_root, tag),
                "w+",
                encoding="utf-8",
            ) as f:
                for sentence in sentences:
                    # TODO(ti250): Assumes tags are plain text
                    sentence_tags = [
                        token[tag] if token[tag] is not None else "😂" for token in sentence.tokens
                    ]
                    f.write(str(("🙃".join(sentence_tags) + "🔥").encode("utf-8")))

        with open(self._document_subsentence_cache_path(cache_location_root), "w+") as f:
            for sentence in sentences:
                indices = []
                for subsentence in sentence.subsentences:
                    indices.append([token.index for token in subsentence.tokens])
                f.write(str(indices) + "\n")

        with open(self._document_subsentence_cache_path(cache_location_root), "w+") as f:
            for sentence in sentences:
                indices = []
                for subsentence in sentence.subsentences:
                    indices.append([token.index for token in subsentence.tokens])
                f.write(str(indices) + "\n")

    def hydrate_document(self, document, document_id, tags=None):
        # Add in all the tags, tokenisation for a document.
        document_configuration = get_document_configuration(document)
        cache_location_root = str(Path(self.cache_location) / self._safe_document_id(document_id))

        # Check cache looks good
        if not Path(cache_location_root).is_dir():
            raise AttributeError(f"{document_id} is not cached")

        with open(self._document_config_path(cache_location_root)) as f:
            cached_configuration = json.load(f)
            if (
                cached_configuration["tokenizer"] != document_configuration["tokenizer"]
                or cached_configuration["taggers"] != document_configuration["taggers"]
            ):
                raise AttributeError(
                    f"Cached value for tokenizers and taggers don't match for {document_id}"
                )

        sentences = document.sentences

        # Add tokenization
        with open(
            self._document_tokenizer_cache_path(
                cache_location_root, document_configuration["tokenizer"]
            )
        ) as f:
            # Need to remove the final element as it will be an empty one
            tokenized_sentences = [sent.split("🙃") for sent in f.read().split("🔥")][:-1]
            for sentence, tokenized_sentence in zip(sentences, tokenized_sentences, strict=False):
                # TODO(ti250): We currently don't retain spans correctly here; what to do? We can always actually cache this...
                toks = [
                    RichToken(
                        text=token,
                        start=-2,
                        end=-1,
                        lexicon=sentence.lexicon,
                        sentence=sentence,
                    )
                    for token in tokenized_sentence
                ]
                sentence._tokens = toks

        # Correct start/end of tokens
        # Save start and end spans
        with open(self._document_tag_cache_path(cache_location_root, "start_end")) as f:
            all_indices = []
            for line in f.readlines():
                line = line.strip()
                if line != "":
                    all_indices.append(json.loads(line))
            for sentence, sent_indices in zip(sentences, all_indices, strict=False):
                for token, indices in zip(sentence.tokens, sent_indices, strict=False):
                    token.start = indices[0]
                    token.end = indices[1]

        # Add tags
        if tags is None:
            tags = ["ner_tag", "pos_tag"]

        for tag_type in tags:
            with open(self._document_tag_cache_path(cache_location_root, tag_type)) as f:
                all_tags = [sent.split("🙃") for sent in f.read().split("🔥")][:-1]
                for sentence, sentence_tags in zip(sentences, all_tags, strict=False):
                    tokens = sentence.tokens
                    for token, tag in zip(tokens, sentence_tags, strict=False):
                        token._tags[tag_type] = tag if tag != "😂" else None

        # Add subsentences
        with open(self._document_subsentence_cache_path(cache_location_root)) as f:
            all_indices = []
            for line in f.readlines():
                line = line.strip()
                if line != "":
                    all_indices.append(json.loads(line))
            for sentence, sent_indices in zip(sentences, all_indices, strict=False):
                subsentences = []
                for subsent_indices in sent_indices:
                    subsent_tokens = [sentence.tokens[index] for index in subsent_indices]
                    subsentences.append(Subsentence(sentence, subsent_tokens))
                if len(subsentences) == 1:
                    subsentences[0]._is_only_subsentence = True
                sentence._subsentences = subsentences

        return document

    def _safe_document_id(self, document_id):
        return document_id.replace(".", "🔥").replace("/", "😅")

    def _document_config_path(self, cache_location_root):
        return str(Path(cache_location_root) / "configuration.json")

    def _document_subsentence_cache_path(self, cache_location_root):
        return str(Path(cache_location_root) / "subsentences.txt")

    def _document_tokenizer_cache_path(self, cache_location_root, tokenizer):
        return str(Path(cache_location_root) / f"tokenizer__{tokenizer}.txt")

    def _document_tag_cache_path(self, cache_location_root, tag):
        return str(Path(cache_location_root) / f"tag__{tag}.txt")
